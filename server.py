from flask import Flask, request, jsonify, send_file
import os
import json
from vcs import VCS

app = Flask(__name__)
vcs = VCS()

@app.route('/push', methods=['POST'])
def push_changes():
    data = request.get_json()
    if not data or 'filename' not in data or 'content' not in data:
        return jsonify({"error": "Invalid data"}), 400
    
    filename = data['filename']
    content = data['content']
    branch = data.get('branch', 'main')  # Default to main branch if not specified
    
    # Switch to specified branch
    try:
        if branch != vcs.current_branch:
            vcs.switch_branch(branch)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    
    # Add file and commit changes
    vcs.add_file(filename, content)
    vcs.commit(f"Updated {filename} from client on branch {branch}")
    return jsonify({"message": "Changes committed successfully."}), 200

@app.route('/branch', methods=['POST'])
def create_branch():
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({"error": "Branch name is required"}), 400
    
    try:
        source_branch = data.get('source')  # Optional source branch
        vcs.create_branch(data['name'], source_branch)
        return jsonify({"message": f"Branch '{data['name']}' created successfully."}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@app.route('/branch/switch', methods=['POST'])
def switch_branch():
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({"error": "Branch name is required"}), 400
    
    try:
        vcs.switch_branch(data['name'])
        return jsonify({"message": f"Switched to branch '{data['name']}'"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@app.route('/branch/merge', methods=['POST'])
def merge_branch():
    data = request.get_json()
    if not data or 'source' not in data:
        return jsonify({"error": "Source branch is required"}), 400
    
    try:
        target_branch = data.get('target')  # Optional target branch
        commit_id = vcs.merge_branch(data['source'], target_branch)
        return jsonify({
            "message": f"Merged branch '{data['source']}' successfully",
            "commit_id": commit_id
        }), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@app.route('/branches', methods=['GET'])
def list_branches():
    return jsonify(vcs.branches), 200

# Existing endpoints remain the same
@app.route('/clone', methods=['GET'])
def clone_repo():
    commits = vcs.commits
    branches = vcs.branches
    return jsonify({
        "commits": commits,
        "branches": branches
    }), 200

@app.route('/pull/<filename>', methods=['GET'])
def pull_changes(filename):
    branch = request.args.get('branch', 'main')  # Get branch from query params
    try:
        if branch != vcs.current_branch:
            vcs.switch_branch(branch)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    file_path = os.path.join(vcs.files_path, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return jsonify({"error": "File not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888)