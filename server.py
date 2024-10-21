from flask import Flask, request, jsonify, send_file
import os
import json
from vcs import VCS
import filecmp
import shutil

app = Flask(__name__)
vcs = VCS()

def detect_changes(branch_name):
    branch_path = vcs.branches[branch_name]['files_path']
    last_commit = vcs.get_latest_commit()
    changes = {}

    if last_commit:
        for filename in os.listdir(branch_path):
            file_path = os.path.join(branch_path, filename)
            if os.path.isfile(file_path):
                if filename in last_commit['snapshot']:
                    old_hash = last_commit['snapshot'][filename]
                    old_file_path = os.path.join(vcs.versions_path, old_hash)
                    if not filecmp.cmp(file_path, old_file_path, shallow=False):
                        with open(file_path, 'r') as f:
                            changes[filename] = f.read()
                else:
                    with open(file_path, 'r') as f:
                        changes[filename] = f.read()
    else:
        for filename in os.listdir(branch_path):
            file_path = os.path.join(branch_path, filename)
            if os.path.isfile(file_path):
                with open(file_path, 'r') as f:
                    changes[filename] = f.read()

    return changes

@app.route('/push', methods=['POST'])
def push_changes():
    try:
        data = request.get_json()
        if not data or 'branch' not in data:
            return jsonify({"error": "Branch name is required"}), 400
        
        branch = data['branch']
        
        if branch not in vcs.branches:
            return jsonify({"error": f"Branch '{branch}' does not exist"}), 400
        
        if branch != vcs.current_branch:
            vcs.switch_branch(branch)
        
        changes = detect_changes(branch)
        
        if not changes:
            return jsonify({"message": "No changes detected"}), 200
        
        for filename, content in changes.items():
            vcs.add_file(filename, content)
        
        commit_message = f"Automatic commit of changes in branch {branch}"
        vcs.commit(commit_message)
        
        return jsonify({
            "message": "Changes committed successfully.",
            "branch": branch,
            "files_changed": list(changes.keys())
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/branch', methods=['POST'])
def create_branch():
    try:
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({"error": "Branch name is required"}), 400
        
        branch_name = data['name']
        source_branch = data.get('source')
        
        vcs.create_branch(branch_name, source_branch)
        return jsonify({
            "message": f"Branch '{branch_name}' created successfully",
            "branch_name": branch_name,
            "source": source_branch
        }), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/branch/switch', methods=['POST'])
def switch_branch():
    try:
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({"error": "Branch name is required"}), 400
        
        vcs.switch_branch(data['name'])
        return jsonify({"message": f"Switched to branch '{data['name']}'"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/branch/merge', methods=['POST'])
def merge_branch():
    try:
        data = request.get_json()
        if not data or 'source' not in data:
            return jsonify({"error": "Source branch is required"}), 400
        
        target_branch = data.get('target')
        commit_id = vcs.merge_branch(data['source'], target_branch)
        return jsonify({
            "message": f"Merged branch '{data['source']}' successfully",
            "commit_id": commit_id
        }), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/branches', methods=['GET'])
def list_branches():
    try:
        return jsonify(vcs.branches), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/clone', methods=['GET'])
def clone_repo():
    try:
        return jsonify({
            "commits": vcs.commits,
            "branches": vcs.branches
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/pull/<filename>', methods=['GET'])
def pull_changes(filename):
    try:
        branch = request.args.get('branch', 'main')
        if branch != vcs.current_branch:
            vcs.switch_branch(branch)
        
        file_path = os.path.join(vcs.get_current_files_path(), filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({"error": "File not found"}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888)