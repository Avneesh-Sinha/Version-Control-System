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
        self.files_path = os.path.join(self.repo_path, 'files')
        self.versions_path = os.path.join(self.repo_path, 'versions')
        self.branches_path = os.path.join(self.repo_path, 'branches.json')
        self.current_branch = 'main'

        os.makedirs(self.commits_path, exist_ok=True)
        os.makedirs(self.files_path, exist_ok=True)
        os.makedirs(self.versions_path, exist_ok=True)
        self.load_branches()

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
        filepath = os.path.join(self.files_path, filename)
        version_path = os.path.join(self.versions_path, file_hash)
        with open(filepath, 'rb') as f:
            content = f.read()
        with open(version_path, 'wb') as vf:
            vf.write(content)

    def restore_version(self, filename, file_hash):
        """Restore a file to a previous version using its hash."""
        version_path = os.path.join(self.versions_path, file_hash)
        filepath = os.path.join(self.files_path, filename)
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
    
    def get_file_content_by_hash(self, file_hash):
        """Retrieve file content based on its hash."""
        # Create a temporary file path to restore the version
        temp_filename = f"temp_{file_hash}"
        self.restore_version(temp_filename, file_hash)  # Restore the version to a temporary file

        # Read the content from the temporary file
        temp_file_path = os.path.join(self.files_path, temp_filename)
        content = self.get_file_content(temp_file_path)

        # Clean up the temporary file after reading
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

        return content if content else None

    
    def load_branches(self):
        """Load branches and set current branch commit history."""
        if os.path.exists(self.branches_path):
            with open(self.branches_path, 'r') as f:
                self.branches = json.load(f)
        else:
            self.branches = {'main': []}
            self.save_branches()

        self.commits = self.branches.get(self.current_branch, [])

    def save_branches(self):
        """Save the branches log to a file."""
        with open(self.branches_path, 'w') as f:
            json.dump(self.branches, f, indent=4)

    def switch_branch(self, branch_name):
        """Switch to another branch."""
        if branch_name not in self.branches:
            print(f"Branch '{branch_name}' does not exist.")
            return

        # Save the current branch's commit history before switching
        self.branches[self.current_branch] = self.commits
        self.current_branch = branch_name
        self.commits = self.branches[branch_name]
        print(f"Switched to branch '{branch_name}'.")

    def create_branch(self, branch_name):
        """Create a new branch."""
        if branch_name in self.branches:
            print(f"Branch '{branch_name}' already exists.")
            return

        self.branches[branch_name] = self.branches[self.current_branch].copy()  # Copy the current branch's history
        self.save_branches()
        print(f"Branch '{branch_name}' created.")

    def commit(self, message):
        """Create a new commit with a message."""
        snapshot = {}
        diff_log = {}
        for filename in os.listdir(self.files_path):
            filepath = os.path.join(self.files_path, filename)
            file_hash = self.hash_file(filepath)

            # Read current version of the file
            new_content = self.get_file_content(filepath)

            # Try to get previous version of the file (from the last commit)
            if self.commits:
                last_commit = self.commits[-1]
                old_file_hash = last_commit['snapshot'].get(filename)
                old_version_path = os.path.join(self.versions_path, old_file_hash) if old_file_hash else None
                old_content = self.get_file_content(old_version_path) if old_version_path else []
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
            'diff_log': diff_log
        }
        self.commits.append(commit_data)
        self.save_commits()
        print(f"Commit {commit_data['id']} created: {message}")

        # Save commits to the current branch
        self.branches[self.current_branch] = self.commits
        self.save_branches()

    def save_commits(self):
        """Save the current branch's commits to the file."""
        branch_commits_file = os.path.join(self.commits_path, f'{self.current_branch}_commits.json')
        with open(branch_commits_file, 'w') as f:
            json.dump(self.commits, f, indent=4)

    def generate_diff(self, old_content, new_content):
            """Generate a diff between two versions of file content."""
            diff = list(difflib.unified_diff(old_content, new_content, lineterm=''))
            return diff if diff else None

    def add_file(self, filename, content):
        """Add a new file to the VCS."""
        filepath = os.path.join(self.files_path, filename)
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"File '{filename}' added to repository.")

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
                print(f"  Chabges in new file -> line {new_line_start}")
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