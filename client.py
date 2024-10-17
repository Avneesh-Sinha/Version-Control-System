import requests
import json

SERVER_URL = "https://c5a6-103-211-18-119.ngrok-free.app/"  # Replace with your ngrok URL
# AUTH_TOKEN = "your_secret_token"  # Same token as in server.py

def push_changes(filename, content):
    url = f"{SERVER_URL}/push"
    # headers = {'Authorization': f'Bearer {AUTH_TOKEN}'}
    data = {'filename': filename, 'content': content}
    
    response = requests.post(url, json=data)
    if response.status_code == 200:
        print("Changes committed successfully.")
    else:
        print("Failed to commit changes:", response.json())

def clone_repo():
    url = f"{SERVER_URL}/clone"
    response = requests.get(url)
    if response.status_code == 200:
        commits = response.json()
        print("Cloned Repository Commits:")
        for commit in commits:
            print(f"Commit ID: {commit['id']}, Message: {commit['message']}")
    else:
        print("Failed to clone repository:", response.json())

def pull_changes(filename):
    """Pull the latest version of the specified file from the server."""
    url = f"{SERVER_URL}/pull/{filename}"
    response = requests.get(url)
    
    if response.status_code == 200:
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"{filename} has been updated with the latest version.")
    else:
        print("Failed to pull changes:", response.json())

# Example usage
if __name__ == "__main__":
    # Pushing changes
    push_changes('example.txt', 'Updated content from client.')
    
    # Cloning the repository
    clone_repo()
    
    # Pulling changes
    pull_changes('example.txt')
