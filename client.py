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

        os.makedirs('files', exist_ok=True)

        # Create or update each file locally
        for filename, content in files.items():
            filepath = os.path.join('files', filename)
            with open(filepath, 'w') as f:
                f.write(content)
            print(f"File '{filename}' updated/created successfully from branch '{branch}'.")

    else:
        error_message = response.json().get('error', 'Unknown error occurred')
        print(f"Failed to pull files: {error_message}")
    
    # if response.status_code == 200:
    #     with open(filename, 'wb') as f:
    #         f.write(response.content)
    #     print(f"{filename} has been updated with the latest version from branch '{branch}'.")
    # else:
    #     print("Failed to pull changes:", response.json())

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
