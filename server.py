from flask import Flask, request, jsonify, send_file
import os
import json
from vcs import VCS
import filecmp
import shutil
import tempfile
import zipfile

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

def ensure_branch_exists(branch_name):
    if branch_name not in vcs.branches:
        vcs.create_branch(branch_name)
        return True
    return False

@app.route('/push', methods=['POST'])
def push_changes():
    try:
        data = request.get_json()
        if not data or 'branch' not in data:
            return jsonify({"error": "Branch name is required"}), 400
        
        branch = data['branch']
        
        branch_created = ensure_branch_exists(branch)
        
        if branch != vcs.current_branch:
            vcs.switch_branch(branch)
        
        changes = detect_changes(branch)
        
        if not changes:
            return jsonify({
                "message": "No changes detected",
                "branch_created": branch_created
            }), 200
        
        for filename, content in changes.items():
            vcs.add_file(filename, content)
        
        commit_message = f"Automatic commit of changes in branch {branch}"
        vcs.commit(commit_message)
        
        return jsonify({
            "message": "Changes committed successfully.",
            "branch": branch,
            "files_changed": list(changes.keys()),
            "branch_created": branch_created
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
        
        branch_name = data['name']
        branch_created = ensure_branch_exists(branch_name)
        vcs.switch_branch(branch_name)
        return jsonify({
            "message": f"Switched to branch '{branch_name}'",
            "branch_created": branch_created
        }), 200
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
        clone_data = {
            "commits": vcs.commits,
            "branches": {}
        }
        
        for branch_name, branch_info in vcs.branches.items():
            current_branch = vcs.current_branch
            vcs.switch_branch(branch_name)
            
            branch_files = {}
            branch_path = vcs.get_current_files_path()
            for root, _, files in os.walk(branch_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r') as f:
                        content = f.read()
                    rel_path = os.path.relpath(file_path, branch_path)
                    branch_files[rel_path] = content
            
            clone_data["branches"][branch_name] = {
                "info": branch_info,
                "files": branch_files
            }
            
            vcs.switch_branch(current_branch)
        
        return jsonify(clone_data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/pull', methods=['GET'])
def pull_changes():
    try:
        branch = request.args.get('branch', 'main')
        if branch not in vcs.branches:
            return jsonify({"error": f"Branch '{branch}' does not exist"}), 404

        # Switch to the requested branch
        current_branch = vcs.current_branch
        vcs.switch_branch(branch)

        # Get all files in the branch
        branch_path = vcs.get_current_files_path()
        files = {}
        for root, _, filenames in os.walk(branch_path):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                with open(file_path, 'r') as f:
                    content = f.read()
                rel_path = os.path.relpath(file_path, branch_path)
                files[rel_path] = content

        # Switch back to the original branch
        vcs.switch_branch(current_branch)

        # Create a temporary zip file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_zip:
            with zipfile.ZipFile(temp_zip, 'w') as zf:
                for filename, content in files.items():
                    zf.writestr(filename, content)

        # Send the zip file
        return send_file(temp_zip.name, mimetype='application/zip', as_attachment=True, download_name=f'{branch}_files.zip')

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888)