import requests
import json
import os

SERVER_URL = "https://0537-103-211-18-24.ngrok-free.app"  # Replace with your ngrok URL

def push_changes(branch):
    """
    Push changes to a specified branch.
    """
    url = f"{SERVER_URL}/push"

    if not os.path.exists('files'):
        print("No 'files' directory found. Please create it and add files to push.")
        return

    # Iterate through all files in the 'files' directory
    for filename in os.listdir('files'):
        file_path = os.path.join('files', filename)
        print("check")
        # Skip if it's not a file
        if not os.path.isfile(file_path):
            continue
        
        # Read the content of the file
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Prepare data to push
        data = {'filename': filename, 'content': content, 'branch': branch}
        
        # Send POST request to push changes
        response = requests.post(url, json=data)
        
        if response.status_code == 200:
            print(f"Changes committed to branch '{branch}' for file '{filename}' successfully.")
        else:
            print(f"Failed to commit changes for file '{filename}':", response.json())

def clone_repo():
    """
    Clone the repository and get the branches and commits.
    """
    url = f"{SERVER_URL}/clone"
    response = requests.get(url)
    
    if response.status_code == 200:
        branches = response.json()
        print("Cloned Repository:")
        for branch, commits in branches.items():
            print(f"Branch: {branch}")
            for commit in commits:
                print(f"  Commit ID: {commit['id']}, Message: {commit['message']}")
    else:
        print("Failed to clone repository:", response.json())

def pull_changes(branch):
    """
    Pull the latest version of the specified file from a specific branch.
    """
    url = f"{SERVER_URL}/pull/{branch}"
    response = requests.get(url)

    if response.status_code == 200:
        files = response.json()

        if not files:
            print(f"No files found for branch '{branch}'.")
            return

        # Ensure 'files' folder exists
        target_dir = 'files'
        os.makedirs(target_dir, exist_ok=True)

        # Get the current set of files in the 'files' directory
        local_files = set(os.listdir(target_dir))

        # Set of files pulled from the server (branch snapshot)
        pulled_files = set(files.keys())

        # Remove files that exist locally but are not present in the pulled branch
        for filename in local_files - pulled_files:
            file_path = os.path.join(target_dir, filename)
            os.remove(file_path)
            print(f"Removed '{filename}' (not in branch '{branch}').")

        # Process and update pulled files
        for filename in pulled_files:
            file_path = os.path.join(target_dir, filename)
            new_content = files[filename]

            # Only write file if content has changed (to minimize file writes)
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    current_content = f.read()
                if current_content == new_content:
                    print(f"'{filename}' is up-to-date.")
                    continue

            # Write updated/new content
            with open(file_path, 'w') as f:
                f.write(new_content)
            print(f"Updated/created '{filename}' with content from branch '{branch}'.")

    else:
        error_message = response.json().get('error', 'Unknown error occurred')
        print(f"Failed to pull files: {error_message}")

def create_branch(branch_name):
    """
    Create a new branch on the server.
    """
    url = f"{SERVER_URL}/create_branch"
    data = {'branch_name': branch_name}
    
    response = requests.post(url, json=data)
    
    if response.status_code == 200:
        print(f"Branch '{branch_name}' created successfully.")
    else:
        print("Failed to create branch:", response.json())

def merge_branches(source_branch, target_branch):
    """
    Request to merge source_branch into target_branch.
    """
    url = f"{SERVER_URL}/merge"
    data = {'source_branch': source_branch, 'target_branch': target_branch}
    
    response = requests.post(url, json=data)
    
    if response.status_code == 200:
        print(f"Successfully merged '{source_branch}' into '{target_branch}'.")
    else:
        print("Merge failed:", response.json())

# Example usage
if __name__ == "__main__":
    # Select branch or create one
    branch = input("Enter the branch to work on (or create): ")
    
    # Create a new branch if necessary
    create_new = input(f"Do you want to create a new branch '{branch}'? (yes/no): ").strip().lower()
    
    if create_new == "yes":
        create_branch(branch)
    
    # Push changes to the specified branch
    # push_changes('example.txt', f"Updated content 4 from client to branch '{branch}'.", branch)
    
    # Cloning the repository
    # clone_repo()
    
    # Pulling changes from the specified branch
    pull_changes(branch)
    # push_changes(branch)
    # merge_branches("sub_main", "main")