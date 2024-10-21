import os
import hashlib
import json
from datetime import datetime
import shutil
import requests
import difflib

class VCS:
    def __init__(self, repo_path='repo'):
        self.repo_path = repo_path
        self.commits_path = os.path.join(self.repo_path, 'commits')
        self.versions_path = os.path.join(self.repo_path, 'versions')
        self.branches_path = os.path.join(self.repo_path, 'branches')
        
        # Create necessary directories
        os.makedirs(self.commits_path, exist_ok=True)
        os.makedirs(self.versions_path, exist_ok=True)
        os.makedirs(self.branches_path, exist_ok=True)
        
        # Initialize branches and load commits
        self.initialize_branches()
        self.load_commits()

    def initialize_branches(self):
        """Initialize branch structure and create main branch if it doesn't exist."""
        self.branches_file = os.path.join(self.branches_path, 'branches.json')
        if not os.path.exists(self.branches_file):
            self.branches = {
                'main': {
                    'name': 'main',
                    'current_commit': None,
                    'commits': [],
                    'files_path': os.path.join(self.branches_path, 'main', 'files')
                }
            }
            self.current_branch = 'main'
            # Create main branch directory
            os.makedirs(self.branches['main']['files_path'], exist_ok=True)
            self.save_branches()
        else:
            self.load_branches()

    def load_branches(self):
        """Load existing branches from the branches file."""
        with open(self.branches_file, 'r') as f:
            self.branches = json.load(f)
        # Set current branch to main if not set
        if not hasattr(self, 'current_branch'):
            self.current_branch = 'main'
        # Ensure all branch directories exist
        for branch in self.branches.values():
            os.makedirs(branch['files_path'], exist_ok=True)

    def save_branches(self):
        """Save branches to the branches file."""
        with open(self.branches_file, 'w') as f:
            json.dump(self.branches, f, indent=4)

    def create_branch(self, branch_name, source_branch=None):
        """Create a new branch from the current or specified branch."""
        if branch_name in self.branches:
            raise ValueError(f"Branch '{branch_name}' already exists")

        source = source_branch if source_branch else self.current_branch
        if source not in self.branches:
            raise ValueError(f"Source branch '{source}' does not exist")

        # Create new branch directory
        new_branch_path = os.path.join(self.branches_path, branch_name, 'files')
        os.makedirs(new_branch_path, exist_ok=True)

        # Copy files from source branch
        source_path = self.branches[source]['files_path']
        if os.path.exists(source_path):
            for item in os.listdir(source_path):
                s = os.path.join(source_path, item)
                d = os.path.join(new_branch_path, item)
                if os.path.isfile(s):
                    shutil.copy2(s, d)

        # Create new branch with same commits as source branch
        self.branches[branch_name] = {
            'name': branch_name,
            'current_commit': self.branches[source]['current_commit'],
            'commits': self.branches[source]['commits'].copy(),
            'files_path': new_branch_path
        }
        self.save_branches()
        print(f"Created new branch '{branch_name}' from '{source}'")

    def switch_branch(self, branch_name):
        """Switch to a different branch."""
        if branch_name not in self.branches:
            raise ValueError(f"Branch '{branch_name}' does not exist")

        # Save current branch state
        self.branches[self.current_branch]['current_commit'] = self.get_latest_commit_id()
        
        # Switch branch
        self.current_branch = branch_name
        
        # Restore files from the latest commit in the new branch
        latest_commit = self.get_latest_commit()
        if latest_commit:
            self.restore_commit_state(latest_commit)
        
        self.save_branches()
        print(f"Switched to branch '{branch_name}'")

    def get_current_files_path(self):
        """Get the files path for the current branch."""
        return self.branches[self.current_branch]['files_path']

    def add_file(self, filename, content):
        """Add a new file to the current branch."""
        filepath = os.path.join(self.get_current_files_path(), filename)
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"File '{filename}' added to branch '{self.current_branch}'.")

    def commit(self, message):
        """Create a new commit with a message in the current branch."""
        files_path = self.get_current_files_path()
        snapshot = {}
        diff_log = {}

        for filename in os.listdir(files_path):
            filepath = os.path.join(files_path, filename)
            file_hash = self.hash_file(filepath)

            # Read current version of the file
            new_content = self.get_file_content(filepath)

            # Try to get previous version of the file
            last_commit = self.get_latest_commit()
            if last_commit and filename in last_commit['snapshot']:
                old_file_hash = last_commit['snapshot'][filename]
                old_version_path = os.path.join(self.versions_path, old_file_hash)
                old_content = self.get_file_content(old_version_path)
            else:
                old_content = []

            # Save file version and generate diff
            self.save_version(filename, file_hash)
            snapshot[filename] = file_hash

            diff = self.generate_diff(old_content, new_content)
            if diff:
                diff_log[filename] = diff

        commit_data = {
            'id': len(self.commits) + 1,
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'snapshot': snapshot,
            'diff_log': diff_log,
            'branch': self.current_branch
        }
        
        self.commits.append(commit_data)
        self.branches[self.current_branch]['commits'].append(commit_data['id'])
        self.branches[self.current_branch]['current_commit'] = commit_data['id']
        
        self.save_commits()
        self.save_branches()
        print(f"Commit {commit_data['id']} created on branch '{self.current_branch}': {message}")

    def merge_branch(self, source_branch, target_branch=None):
        """Merge source branch into target branch (defaults to current branch)."""
        if source_branch not in self.branches:
            raise ValueError(f"Source branch '{source_branch}' does not exist")

        target = target_branch if target_branch else self.current_branch
        if target not in self.branches:
            raise ValueError(f"Target branch '{target}' does not exist")

        source_files_path = self.branches[source_branch]['files_path']
        target_files_path = self.branches[target]['files_path']

        # Create a new commit for the merge
        merge_message = f"Merged branch '{source_branch}' into '{target}'"
        
        # Copy all files from source branch to target branch
        for filename in os.listdir(source_files_path):
            source_file = os.path.join(source_files_path, filename)
            target_file = os.path.join(target_files_path, filename)
            if os.path.isfile(source_file):
                shutil.copy2(source_file, target_file)

        # Create merge commit
        current_branch = self.current_branch
        self.current_branch = target  # Temporarily switch to target branch
        commit_id = self.commit(merge_message)
        self.current_branch = current_branch  # Switch back

        return commit_id

    def load_commits(self):
        """Load existing commits from the commits log."""
        self.commits = []
        commits_file = os.path.join(self.commits_path, 'commits.json')
        if os.path.exists(commits_file):
            with open(commits_file, 'r') as f:
                self.commits = json.load(f)

    def save_commits(self):
        """Save the commits log to a file."""
        commits_file = os.path.join(self.commits_path, 'commits.json')
        with open(commits_file, 'w') as f:
            json.dump(self.commits, f, indent=4)

    def hash_file(self, filepath):
        """Generate a hash for the file content to track changes."""
        hasher = hashlib.sha256()
        with open(filepath, 'rb') as f:
            hasher.update(f.read())
        return hasher.hexdigest()

    def save_version(self, filename, file_hash):
        """Save a version of the file with a unique hash."""
        filepath = os.path.join(self.get_current_files_path(), filename)
        version_path = os.path.join(self.versions_path, file_hash)
        with open(filepath, 'rb') as f:
            content = f.read()
        with open(version_path, 'wb') as vf:
            vf.write(content)

    def restore_version(self, filename, file_hash):
        """Restore a file to a previous version using its hash."""
        version_path = os.path.join(self.versions_path, file_hash)
        filepath = os.path.join(self.get_current_files_path(), filename)
        if os.path.exists(version_path):
            with open(version_path, 'rb') as vf:
                content = vf.read()
            with open(filepath, 'wb') as f:
                f.write(content)
            print(f"Restored '{filename}' to version with hash {file_hash}.")
        else:
            print(f"Version with hash {file_hash} not found.")

    def get_file_content(self, filepath):
        """Read file content if it exists."""
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return f.readlines()
        return []

    def generate_diff(self, old_content, new_content):
        """Generate a diff between two versions of file content."""
        diff = list(difflib.unified_diff(old_content, new_content, lineterm=''))
        return diff if diff else None

    def get_latest_commit_id(self):
        """Get the ID of the latest commit in the current branch."""
        branch_commits = self.branches[self.current_branch]['commits']
        return branch_commits[-1] if branch_commits else None

    def get_latest_commit(self):
        """Get the latest commit object in the current branch."""
        latest_id = self.get_latest_commit_id()
        return self.get_commit_by_id(latest_id) if latest_id else None

    def get_commit_by_id(self, commit_id):
        """Get a commit object by its ID."""
        return next((commit for commit in self.commits if commit['id'] == commit_id), None)

    def restore_commit_state(self, commit):
        """Restore the repository state to a specific commit."""
        if not commit:
            return

        # Clear current files
        current_files_path = self.get_current_files_path()
        for file in os.listdir(current_files_path):
            os.remove(os.path.join(current_files_path, file))

        # Restore files from commit
        for filename, file_hash in commit['snapshot'].items():
            self.restore_version(filename, file_hash)

    def view_history(self):
        """Display the commit history in a human-readable format."""
        if not self.commits:
            print("No commits found.")
            return
        for commit in self.commits:
            print(f"Commit ID: {commit['id']}")
            print(f"Timestamp: {commit['timestamp']}")
            print(f"Message: {commit['message']}")
            print("Changes:")
            for filename, diff in commit.get('diff_log', {}).items():
                print(f"  File: {filename}")
                self.format_diff(diff)
            print('-' * 30)

    def format_diff(self, diff):
        """Format the diff output to be more human-readable."""
        added_lines = []
        removed_lines = []
        
        for line in diff:
            if line.startswith('@@'):
                # Extract information about line numbers (ignore for simple output)
                line_info = line.split(' ')
                old_info = line_info[1]  # e.g. -1
                new_info = line_info[2]  # e.g. +1,2
                
                # Extract the line numbers from this part
                old_line_start = int(old_info.split(',')[0][1:])  # remove the '-' and get number
                new_line_start = int(new_info.split(',')[0][1:])  # remove the '+' and get number
                new_line_count = int(new_info.split(',')[1]) if ',' in new_info else 1
                
                print(f"  Changes in old file -> line {old_line_start}")
                print(f"  Changes in new file -> line {new_line_start}")
                print(f"  New version has {new_line_count} lines starting from line {new_line_start}")
                
            elif line.startswith('-'):
                removed_lines.append(line[1:].strip())  # Remove the "-" and strip whitespace
            elif line.startswith('+'):
                added_lines.append(line[1:].strip())  # Remove the "+" and strip whitespace
        
        if removed_lines:
            print(f"  Removed lines:")
            for removed in removed_lines[1:]:
                print(f"    - {removed}")
        
        if added_lines:
            print(f"  Added lines:")
            for added in added_lines[1:]:
                print(f"    + {added}")

    def push_changes(self, remote_url):
        """Push changes to the remote server."""
        response = requests.post(remote_url, data={"commits": json.dumps(self.commits)})
        print(response.text)

    def pull_changes(self, remote_url):
        """Pull changes from the remote server."""
        response = requests.get(remote_url)
        remote_commits = json.loads(response.text)
        # Apply the new commits here, you could also check for conflicts
        print(f"Pulled changes: {remote_commits}")

# Example usage
vcs = VCS()
vcs.view_history()