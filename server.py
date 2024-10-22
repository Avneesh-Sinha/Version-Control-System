from flask import Flask, request, jsonify, send_file
import os
import json
from vcs import VCS

app = Flask(__name__)

# Initialize the VCS
vcs = VCS()

@app.route('/push', methods=['POST'])
def push_changes():
    """
    Handle client push requests and manually authorize changes to be committed.
    """
    # Get the data from the request (filename, content, branch)
    data = request.get_json()
    
    if not data or 'filename' not in data or 'content' not in data or 'branch' not in data:
        return jsonify({"error": "Invalid data. Requires 'filename', 'content', and 'branch'."}), 400

    branch = data['branch']
    filename = data['filename']
    content = data['content']

    # Check if the branch exists; if not, return an error
    if branch not in vcs.branches:
        return jsonify({"error": f"Branch '{branch}' does not exist."}), 404

    # Prompt server administrator for manual authorization
    # print(f"Client is trying to push changes to branch '{branch}'. Authorize the push? (yes/no):")
    # user_input = input().strip().lower()

    # if user_input != "yes":
    #     return jsonify({"message": "Push denied by server."}), 403

    # Switch to the target branch
    vcs.switch_branch(branch)

    # Add the file to the VCS and commit the changes
    vcs.add_file(filename, content)
    vcs.commit(f"Updated {filename} on branch '{branch}' from client.")

    return jsonify({"message": f"Changes committed to branch '{branch}' successfully."}), 200

@app.route('/clone', methods=['GET'])
def clone_repo():
    """
    Handle repo cloning by returning the commit history and branch structure.
    """
    return jsonify(vcs.branches), 200

@app.route('/pull/<branch>', methods=['GET'])
def pull_changes(branch):
    """
    Pull the latest version of the specified file from a specific branch.
    """
    if branch not in vcs.branches:
        return jsonify({"error": f"Branch '{branch}' does not exist."}), 404

    # Switch to the target branch
    vcs.switch_branch(branch)

    # Get the snapshot for the branch
    branch_snapshots = vcs.branches.get(branch, {})
    
    if not branch_snapshots:
        return jsonify({"error": f"No files found for branch '{branch}'."}), 404

    # Create a dictionary to hold the file contents
    files = {}
    
    for snapshot in branch_snapshots:
        for filename, file_hash in snapshot['snapshot'].items():
            # Get the content of the file based on its hash
            file_content = vcs.get_file_content_by_hash(file_hash)
            files[filename] = ''.join(file_content)  # Convert list to string

    # Return the list of all files and their contents in the branch
    return jsonify(files), 200

    # file_path = os.path.join(vcs.files_path, filename)
    
    # if os.path.exists(file_path):
    #     return send_file(file_path, as_attachment=True)
    # else:
    #     return jsonify({"error": "File not found"}), 404

@app.route('/create_branch', methods=['POST'])
def create_branch():
    """
    Create a new branch in the repository.
    """
    data = request.get_json()
    
    if 'branch_name' not in data:
        return jsonify({"error": "Branch name is required."}), 400

    branch_name = data['branch_name']

    # Create a new branch
    success = vcs.create_branch(branch_name)
    
    if success:
        return jsonify({"message": f"Branch '{branch_name}' created successfully."}), 200
    else:
        return jsonify({"error": f"Branch '{branch_name}' already exists."}), 400

@app.route('/merge', methods=['POST'])
def merge():
    """
    Merge source_branch into target_branch.
    """
    data = request.get_json()
    source_branch = data.get('source_branch')
    target_branch = data.get('target_branch')

    try:
        vcs.merge(source_branch, target_branch)
        return jsonify({"message": f"Successfully merged {source_branch} into {target_branch}."}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888)  # Adjust port as needed
