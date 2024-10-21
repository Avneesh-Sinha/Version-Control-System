import requests
import json

SERVER_URL = "https://b1b4-103-211-18-24.ngrok-free.app"  # Replace with your ngrok URL

def push_changes(filename, content, branch):
    """
    Push changes to a specified branch.
    """
    url = f"{SERVER_URL}/push"
    data = {'filename': filename, 'content': content, 'branch': branch}
    
    response = requests.post(url, json=data)
    
    if response.status_code == 200:
        print(f"Changes committed to branch '{branch}' successfully.")
    else:
        print("Failed to commit changes:", response.json())

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

def pull_changes(filename, branch):
    """
    Pull the latest version of the specified file from a specific branch.
    """
    url = f"{SERVER_URL}/pull/{branch}/{filename}"
    response = requests.get(url)
    
    if response.status_code == 200:
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"{filename} has been updated with the latest version from branch '{branch}'.")
    else:
        print("Failed to pull changes:", response.json())

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
    push_changes('example.txt', f"Updated content from client to branch '{branch}'.", branch)
    
    # Cloning the repository
    clone_repo()
    
    # Pulling changes from the specified branch
    pull_changes('example.txt', branch)
