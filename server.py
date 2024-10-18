from flask import Flask, request, jsonify, send_file
import os
import json
from vcs import VCS

app = Flask(__name__)
vcs = VCS()

# Simple authorization token (replace with a more secure method in production)
# AUTH_TOKEN = "your_secret_token"

@app.route('/push', methods=['POST'])
def push_changes():
    # Check for authorization
    # token = request.headers.get('Authorization')
    # if token != f"Bearer {AUTH_TOKEN}":
    #     return jsonify({"error": "Unauthorized"}), 401

    # Get the data from the request
    data = request.get_json()
    if not data or 'filename' not in data or 'content' not in data:
        return jsonify({"error": "Invalid data"}), 400
    
    # Prompt server administrator for manual authorization
    print("Client is trying to push changes. Authorize the push? (yes/no):")
    user_input = input().strip().lower()

    if user_input != "yes":
        return jsonify({"message": "Push denied by server."}), 403

    # Add the file to the VCS and commit the changes
    filename = data['filename']
    content = data['content']

    vcs.add_file(filename, content)
    vcs.commit(f"Updated {filename} from client.")

    return jsonify({"message": "Changes committed successfully."}), 200

@app.route('/clone', methods=['GET'])
def clone_repo():
    # Clone repository functionality
    commits = vcs.commits
    return jsonify(commits), 200

@app.route('/pull/<filename>', methods=['GET'])
def pull_changes(filename):
    """Pull the latest version of the specified file."""
    file_path = os.path.join(vcs.files_path, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return jsonify({"error": "File not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888)  # Adjust port as needed
