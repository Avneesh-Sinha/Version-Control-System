from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# Path to where you'll store incoming files
REPO_PATH = 'repo/files'

if not os.path.exists(REPO_PATH):
    os.makedirs(REPO_PATH)

@app.route('/push', methods=['POST'])
def push_changes():
    """Receive file updates from the client."""
    data = request.json
    filename = data.get('filename')
    content = data.get('content')

    if not filename or not content:
        return jsonify({'error': 'Missing filename or content'}), 400

    # Save the file to your repository
    filepath = os.path.join(REPO_PATH, filename)
    with open(filepath, 'w') as f:
        f.write(content)

    return jsonify({'status': f'File {filename} updated successfully'}), 200

@app.route('/pull', methods=['GET'])
def pull_changes():
    """Allow the client to pull the latest version of the file."""
    filename = request.args.get('filename')

    if not filename:
        return jsonify({'error': 'Missing filename'}), 400

    filepath = os.path.join(REPO_PATH, filename)
    if not os.path.exists(filepath):
        return jsonify({'error': f'File {filename} not found'}), 404

    with open(filepath, 'r') as f:
        content = f.read()

    return jsonify({'filename': filename, 'content': content}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
