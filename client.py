import requests

# Change this to your server's IP address
SERVER_URL = 'http://127.0.0.1:8000'

def push_changes(filename, content):
    """Push changes to the remote server."""
    url = f'{SERVER_URL}/push'
    data = {'filename': filename, 'content': content}
    response = requests.post(url, json=data)

    if response.status_code == 200:
        print(f"File '{filename}' pushed successfully.")
    else:
        print(f"Error: {response.json().get('error')}")

def pull_changes(filename):
    """Pull the latest changes from the remote server."""
    url = f'{SERVER_URL}/pull'
    params = {'filename': filename}
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        print(f"Pulled file '{data['filename']}':\n{data['content']}")
    else:
        print(f"Error: {response.json().get('error')}")

if __name__ == '__main__':
    # Example usage
    push_changes('example.txt', 'Content from client Gaurav\'s system.')
    pull_changes('example.txt')
