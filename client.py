import requests
import json
import os

class VCSClient:
    def __init__(self, server_url):
        self.server_url = server_url.rstrip('/')
        self.local_path = 'local_repo'
        os.makedirs(self.local_path, exist_ok=True)

    def push_changes(self, filename, content, branch='main'):
        """Push changes to a specific branch."""
        url = f"{self.server_url}/push"
        data = {
            'filename': filename,
            'content': content,
            'branch': branch
        }
        
        response = requests.post(url, json=data)
        if response.status_code == 200:
            print(f"Changes committed successfully to branch '{branch}'.")
        else:
            print("Failed to commit changes:", response.json())

    def create_branch(self, branch_name, source_branch=None):
        """Create a new branch."""
        url = f"{self.server_url}/branch"
        data = {
            'name': branch_name,
            'source': source_branch
        }
        
        response = requests.post(url, json=data)
        if response.status_code == 200:
            print(f"Branch '{branch_name}' created successfully.")
        else:
            print("Failed to create branch:", response.json())

    def switch_branch(self, branch_name):
        """Switch to a different branch."""
        url = f"{self.server_url}/branch/switch"
        data = {'name': branch_name}
        
        response = requests.post(url, json=data)
        if response.status_code == 200:
            print(f"Switched to branch '{branch_name}'.")
        else:
            print("Failed to switch branch:", response.json())

    def merge_branch(self, source_branch, target_branch=None):
        """Merge source branch into target branch."""
        url = f"{self.server_url}/branch/merge"
        data = {
            'source': source_branch,
            'target': target_branch
        }
        
        response = requests.post(url, json=data)
        if response.status_code == 200:
            result = response.json()
            print(f"Merged branch '{source_branch}' successfully. Commit ID: {result['commit_id']}")
        else:
            print("Failed to merge branch:", response.json())

    def list_branches(self):
        """Get list of all branches."""
        url = f"{self.server_url}/branches"
        response = requests.get(url)
        
        if response.status_code == 200:
            branches = response.json()
            print("\nAvailable branches:")
            for branch_name, branch_info in branches.items():
                current_commit = branch_info.get('current_commit', 'No commits')
                print(f"- {branch_name} (Current commit: {current_commit})")
        else:
            print("Failed to fetch branches:", response.json())

    def clone_repo(self):
        """Clone the entire repository."""
        url = f"{self.server_url}/clone"
        response = requests.get(url)
        
        if response.status_code == 200:
            repo_data = response.json()
            print("\nRepository cloned successfully:")
            print("\nCommits:")
            for commit in repo_data['commits']:
                print(f"ID: {commit['id']}")
                print(f"Message: {commit['message']}")
                print(f"Branch: {commit.get('branch', 'main')}")
                print(f"Timestamp: {commit['timestamp']}")
                print("-" * 40)
            
            print("\nBranches:")
            for branch_name, branch_info in repo_data['branches'].items():
                print(f"- {branch_name} (Current commit: {branch_info.get('current_commit', 'No commits')})")
        else:
            print("Failed to clone repository:", response.json())

    def pull_changes(self, filename, branch='main'):
        """Pull the latest version of a file from a specific branch."""
        url = f"{self.server_url}/pull/{filename}"
        params = {'branch': branch}
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            local_path = os.path.join(self.local_path, filename)
            with open(local_path, 'wb') as f:
                f.write(response.content)
            print(f"Successfully pulled '{filename}' from branch '{branch}'")
        else:
            print("Failed to pull changes:", response.json())

def main():
    # Replace with your ngrok URL
    SERVER_URL = "https://c5a6-103-211-18-119.ngrok-free.app"
    client = VCSClient(SERVER_URL)

    while True:
        print("\nVCS Client Menu:")
        print("1. Push changes")
        print("2. Create new branch")
        print("3. Switch branch")
        print("4. Merge branch")
        print("5. List branches")
        print("6. Clone repository")
        print("7. Pull changes")
        print("8. Exit")

        choice = input("\nEnter your choice (1-8): ")

        if choice == '1':
            filename = input("Enter filename: ")
            content = input("Enter content: ")
            branch = input("Enter branch name (press Enter for main): ") or 'main'
            client.push_changes(filename, content, branch)

        elif choice == '2':
            branch_name = input("Enter new branch name: ")
            source = input("Enter source branch (press Enter for current branch): ")
            client.create_branch(branch_name, source if source else None)

        elif choice == '3':
            branch_name = input("Enter branch name to switch to: ")
            client.switch_branch(branch_name)

        elif choice == '4':
            source = input("Enter source branch name: ")
            target = input("Enter target branch name (press Enter for current branch): ")
            client.merge_branch(source, target if target else None)

        elif choice == '5':
            client.list_branches()

        elif choice == '6':
            client.clone_repo()

        elif choice == '7':
            filename = input("Enter filename to pull: ")
            branch = input("Enter branch name (press Enter for main): ") or 'main'
            client.pull_changes(filename, branch)

        elif choice == '8':
            print("Goodbye!")
            break

        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()