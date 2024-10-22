import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QLineEdit, QTextEdit, 
                           QLabel, QComboBox, QFileDialog, QMessageBox, 
                           QListWidget, QTabWidget, QSplitter, QGroupBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor
import os
import requests
import json

class GitClientGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Modern Git Client")
        self.setMinimumSize(900, 600)
        
        # Set the style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
            }
            QLabel {
                color: #ffffff;
                font-size: 14px;
            }
            QPushButton {
                background-color: #0d6efd;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #0b5ed7;
            }
            QPushButton:pressed {
                background-color: #0a58ca;
            }
            QLineEdit, QTextEdit, QComboBox {
                background-color: #363636;
                border: 1px solid #474747;
                color: white;
                padding: 6px;
                border-radius: 4px;
            }
            QListWidget {
                background-color: #363636;
                color: white;
                border: 1px solid #474747;
                border-radius: 4px;
            }
            QTabWidget::pane {
                border: 1px solid #474747;
                background-color: #2b2b2b;
            }
            QTabBar::tab {
                background-color: #363636;
                color: white;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #0d6efd;
            }
            QGroupBox {
                color: white;
                border: 1px solid #474747;
                border-radius: 4px;
                margin-top: 1em;
                padding-top: 1em;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 3px;
            }
        """)

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Create tab widget
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)

        # Repository Tab
        repo_tab = QWidget()
        repo_layout = QVBoxLayout(repo_tab)

        # Branch controls
        branch_layout = QHBoxLayout()
        self.branch_combo = QComboBox()
        self.branch_combo.setMinimumWidth(200)
        self.new_branch_input = QLineEdit()
        self.new_branch_input.setPlaceholderText("New branch name")
        create_branch_btn = QPushButton("Create Branch")
        create_branch_btn.clicked.connect(self.create_branch)
        
        branch_layout.addWidget(QLabel("Current Branch:"))
        branch_layout.addWidget(self.branch_combo)
        branch_layout.addWidget(self.new_branch_input)
        branch_layout.addWidget(create_branch_btn)
        branch_layout.addStretch()
        repo_layout.addLayout(branch_layout)

        # Repository content
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # File list
        file_widget = QWidget()
        file_layout = QVBoxLayout(file_widget)
        file_layout.addWidget(QLabel("Files:"))
        self.file_list = QListWidget()
        file_layout.addWidget(self.file_list)
        
        # File content
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.addWidget(QLabel("File Content:"))
        self.content_edit = QTextEdit()
        content_layout.addWidget(self.content_edit)
        
        content_splitter.addWidget(file_widget)
        content_splitter.addWidget(content_widget)
        repo_layout.addWidget(content_splitter)

        # Action buttons
        button_layout = QHBoxLayout()
        pull_btn = QPushButton("Pull Changes")
        push_btn = QPushButton("Push Changes")
        refresh_btn = QPushButton("Refresh")
        
        pull_btn.clicked.connect(self.pull_changes)
        push_btn.clicked.connect(self.push_changes)
        refresh_btn.clicked.connect(self.refresh_repo)
        
        button_layout.addWidget(pull_btn)
        button_layout.addWidget(push_btn)
        button_layout.addWidget(refresh_btn)
        button_layout.addStretch()
        repo_layout.addLayout(button_layout)

        # Merge Tab with improved layout
        merge_tab = QWidget()
        merge_layout = QVBoxLayout(merge_tab)

        # Branch Selection Group
        branch_group = QGroupBox("Branch Selection")
        branch_group_layout = QVBoxLayout(branch_group)

        # Source branch selection
        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel("Source Branch:"))
        self.source_branch_combo = QComboBox()
        self.source_branch_combo.setMinimumWidth(200)
        source_layout.addWidget(self.source_branch_combo)
        source_layout.addStretch()
        branch_group_layout.addLayout(source_layout)

        # Source branch info
        self.source_info = QTextEdit()
        self.source_info.setPlaceholderText("Source branch information will appear here...")
        self.source_info.setMaximumHeight(100)
        self.source_info.setReadOnly(True)
        branch_group_layout.addWidget(self.source_info)

        # Target branch selection
        target_layout = QHBoxLayout()
        target_layout.addWidget(QLabel("Target Branch:"))
        self.target_branch_combo = QComboBox()
        self.target_branch_combo.setMinimumWidth(200)
        target_layout.addWidget(self.target_branch_combo)
        target_layout.addStretch()
        branch_group_layout.addLayout(target_layout)

        # Target branch info
        self.target_info = QTextEdit()
        self.target_info.setPlaceholderText("Target branch information will appear here...")
        self.target_info.setMaximumHeight(100)
        self.target_info.setReadOnly(True)
        branch_group_layout.addWidget(self.target_info)

        merge_layout.addWidget(branch_group)

        # Merge Preview Group
        preview_group = QGroupBox("Merge Preview")
        preview_layout = QVBoxLayout(preview_group)

        # Changes list
        preview_layout.addWidget(QLabel("Changes to be merged:"))
        self.changes_list = QListWidget()
        preview_layout.addWidget(self.changes_list)

        # Conflict warning
        self.conflict_label = QLabel("")
        self.conflict_label.setStyleSheet("color: #ffc107;")  # Warning color
        preview_layout.addWidget(self.conflict_label)

        merge_layout.addWidget(preview_group)

        # Action buttons
        merge_button_layout = QHBoxLayout()
        
        # Compare button
        compare_btn = QPushButton("Compare Branches")
        compare_btn.clicked.connect(self.compare_branches)
        merge_button_layout.addWidget(compare_btn)
        
        # Merge button
        merge_btn = QPushButton("Merge Branches")
        merge_btn.clicked.connect(self.merge_branches)
        merge_button_layout.addWidget(merge_btn)
        
        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
            }
            QPushButton:hover {
                background-color: #bb2d3b;
            }
        """)
        cancel_btn.clicked.connect(self.cancel_merge)
        merge_button_layout.addWidget(cancel_btn)
        
        merge_button_layout.addStretch()
        merge_layout.addLayout(merge_button_layout)

        # Add tabs to tab widget
        tab_widget.addTab(repo_tab, "Repository")
        tab_widget.addTab(merge_tab, "Merge")

        # Initialize data
        self.refresh_repo()
        self.file_list.itemClicked.connect(self.show_file_content)
        
        # Connect branch selection change events
        self.source_branch_combo.currentTextChanged.connect(self.update_branch_info)
        self.target_branch_combo.currentTextChanged.connect(self.update_branch_info)

    def refresh_repo(self):
        try:
            response = requests.get(f"{SERVER_URL}/clone")
            if response.status_code == 200:
                branches = response.json()
                self.branch_combo.clear()
                self.source_branch_combo.clear()
                self.target_branch_combo.clear()
                
                for branch in branches.keys():
                    self.branch_combo.addItem(branch)
                    self.source_branch_combo.addItem(branch)
                    self.target_branch_combo.addItem(branch)
                
                self.refresh_files()
            else:
                self.show_error("Failed to refresh repository")
        except Exception as e:
            self.show_error(f"Error refreshing repository: {str(e)}")

    def refresh_files(self):
        current_branch = self.branch_combo.currentText()
        if not current_branch:
            return

        try:
            response = requests.get(f"{SERVER_URL}/pull/{current_branch}")
            if response.status_code == 200:
                files = response.json()
                self.file_list.clear()
                for filename in files.keys():
                    self.file_list.addItem(filename)
            else:
                self.show_error("Failed to fetch files")
        except Exception as e:
            self.show_error(f"Error fetching files: {str(e)}")

    def show_file_content(self, item):
        current_branch = self.branch_combo.currentText()
        filename = item.text()
        
        try:
            response = requests.get(f"{SERVER_URL}/pull/{current_branch}")
            if response.status_code == 200:
                files = response.json()
                if filename in files:
                    self.content_edit.setText(files[filename])
            else:
                self.show_error("Failed to fetch file content")
        except Exception as e:
            self.show_error(f"Error fetching file content: {str(e)}")

    def create_branch(self):
        branch_name = self.new_branch_input.text().strip()
        if not branch_name:
            self.show_error("Please enter a branch name")
            return

        try:
            response = requests.post(f"{SERVER_URL}/create_branch", 
                                  json={'branch_name': branch_name})
            if response.status_code == 200:
                self.show_message("Success", f"Branch '{branch_name}' created successfully")
                self.refresh_repo()
                self.new_branch_input.clear()
            else:
                self.show_error("Failed to create branch")
        except Exception as e:
            self.show_error(f"Error creating branch: {str(e)}")

    def pull_changes(self):
        current_branch = self.branch_combo.currentText()
        if not current_branch:
            self.show_error("Please select a branch")
            return

        try:
            response = requests.get(f"{SERVER_URL}/pull/{current_branch}")
            if response.status_code == 200:
                files = response.json()
                if not files:
                    print(f"No files found for branch '{current_branch}'.")
                    return

                # Ensure 'files' folder exists
                target_dir = 'files'
                os.makedirs(target_dir, exist_ok=True)

                # Get the current set of files in the 'files' directory
                local_files = set(os.listdir(target_dir))

                # Set of files pulled from the server (branch snapshot)
                pulled_files = set(files.keys())

                # Remove files that exist locally but are not present in the pulled branch
                for filename in local_files - pulled_files:
                    file_path = os.path.join(target_dir, filename)
                    os.remove(file_path)
                    print(f"Removed '{filename}' (not in branch '{current_branch}').")

                # Process and update pulled files
                for filename in pulled_files:
                    file_path = os.path.join(target_dir, filename)
                    new_content = files[filename]

                    # Only write file if content has changed (to minimize file writes)
                    if os.path.exists(file_path):
                        with open(file_path, 'r') as f:
                            current_content = f.read()
                        if current_content == new_content:
                            print(f"'{filename}' is up-to-date.")
                            continue

                    # Write updated/new content
                    with open(file_path, 'w') as f:
                        f.write(new_content)
                    print(f"Updated/created '{filename}' with content from branch '{current_branch}'.")
                self.show_message("Success", "Changes pulled successfully")
                self.refresh_files()
            else:
                self.show_error("Failed to pull changes")
        except Exception as e:
            self.show_error(f"Error pulling changes: {str(e)}")

    def push_changes(self):
        url = f"{SERVER_URL}/push"
        branch = self.branch_combo.currentText()
        if not branch:
            self.show_error("Please select a branch")
            return
        if not os.path.exists('files'):
            print("No 'files' directory found. Please create it and add files to push.")
            return

        # Iterate through all files in the 'files' directory
        for filename in os.listdir('files'):
            file_path = os.path.join('files', filename)
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
                self.show_message("Success", "Changes pushed successfully")
                self.refresh_files()
        else:
            self.show_error("Failed to push changes")

    def update_branch_info(self):
        """Update the information displayed for selected branches"""
        source_branch = self.source_branch_combo.currentText()
        target_branch = self.target_branch_combo.currentText()
        
        if source_branch:
            try:
                response = requests.get(f"{SERVER_URL}/pull/{source_branch}")
                if response.status_code == 200:
                    files = response.json()
                    self.source_info.setText(f"Branch: {source_branch}\n"
                                          f"Number of files: {len(files)}")
            except Exception:
                self.source_info.setText("Unable to fetch branch information")

        if target_branch:
            try:
                response = requests.get(f"{SERVER_URL}/pull/{target_branch}")
                if response.status_code == 200:
                    files = response.json()
                    self.target_info.setText(f"Branch: {target_branch}\n"
                                          f"Number of files: {len(files)}")
            except Exception:
                self.target_info.setText("Unable to fetch branch information")

    def compare_branches(self):
        """Compare the selected source and target branches"""
        source_branch = self.source_branch_combo.currentText()
        target_branch = self.target_branch_combo.currentText()
        
        if source_branch == target_branch:
            self.show_error("Source and target branches must be different")
            return

        try:
            # Get files from both branches
            source_response = requests.get(f"{SERVER_URL}/pull/{source_branch}")
            target_response = requests.get(f"{SERVER_URL}/pull/{target_branch}")
            
            if source_response.status_code == 200 and target_response.status_code == 200:
                source_files = source_response.json()
                target_files = target_response.json()
                
                self.changes_list.clear()
                conflicts = []
                
                # Compare files
                all_files = set(source_files.keys()) | set(target_files.keys())
                
                for file in all_files:
                    if file in source_files and file in target_files:
                        if source_files[file] != target_files[file]:
                            self.changes_list.addItem(f"Modified: {file}")
                            conflicts.append(file)
                    elif file in source_files:
                        self.changes_list.addItem(f"Added in source: {file}")
                    else:
                        self.changes_list.addItem(f"Added in target: {file}")
                
                # Update conflict label
                if conflicts:
                    self.conflict_label.setText(f"⚠️ Warning: {len(conflicts)} potential conflict(s) detected")
                else:
                    self.conflict_label.setText("✓ No conflicts detected")
                
                # Show summary
                self.changes_list.addItem("")
                self.changes_list.addItem("Summary:")
                self.changes_list.addItem(f"Total changes: {len(all_files)}")
                self.changes_list.addItem(f"Potential conflicts: {len(conflicts)}")
            else:
                self.show_error("Failed to compare branches")
        except Exception as e:
            self.show_error(f"Error comparing branches: {str(e)}")

    def cancel_merge(self):
        """Cancel the merge operation"""
        self.changes_list.clear()
        self.conflict_label.setText("")
        self.source_info.clear()
        self.target_info.clear()

    def refresh_repo(self):
        try:
            response = requests.get(f"{SERVER_URL}/clone")
            if response.status_code == 200:
                branches = response.json()
                self.branch_combo.clear()
                self.source_branch_combo.clear()
                self.target_branch_combo.clear()
                
                for branch in branches.keys():
                    self.branch_combo.addItem(branch)
                    self.source_branch_combo.addItem(branch)
                    self.target_branch_combo.addItem(branch)
                
                self.refresh_files()
            else:
                self.show_error("Failed to refresh repository")
        except Exception as e:
            self.show_error(f"Error refreshing repository: {str(e)}")

    def refresh_files(self):
        current_branch = self.branch_combo.currentText()
        if not current_branch:
            return

        try:
            response = requests.get(f"{SERVER_URL}/pull/{current_branch}")
            if response.status_code == 200:
                files = response.json()
                self.file_list.clear()
                for filename in files.keys():
                    self.file_list.addItem(filename)
            else:
                self.show_error("Failed to fetch files")
        except Exception as e:
            self.show_error(f"Error fetching files: {str(e)}")

    def show_file_content(self, item):
        current_branch = self.branch_combo.currentText()
        filename = item.text()
        
        try:
            response = requests.get(f"{SERVER_URL}/pull/{current_branch}")
            if response.status_code == 200:
                files = response.json()
                if filename in files:
                    self.content_edit.setText(files[filename])
            else:
                self.show_error("Failed to fetch file content")
        except Exception as e:
            self.show_error(f"Error fetching file content: {str(e)}")

    def create_branch(self):
        branch_name = self.new_branch_input.text().strip()
        if not branch_name:
            self.show_error("Please enter a branch name")
            return

        try:
            response = requests.post(f"{SERVER_URL}/create_branch", 
                                  json={'branch_name': branch_name})
            if response.status_code == 200:
                self.show_message("Success", f"Branch '{branch_name}' created successfully")
                self.refresh_repo()
                self.new_branch_input.clear()
            else:
                self.show_error("Failed to create branch")
        except Exception as e:
            self.show_error(f"Error creating branch: {str(e)}")

    def merge_branches(self):
        """Merge the selected source branch into the target branch"""
        source_branch = self.source_branch_combo.currentText()
        target_branch = self.target_branch_combo.currentText()
        
        if source_branch == target_branch:
            self.show_error("Source and target branches must be different")
            return

        # Show confirmation dialog
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setText(f"Are you sure you want to merge '{source_branch}' into '{target_branch}'?")
        msg.setInformativeText("This action cannot be undone!")
        msg.setWindowTitle("Confirm Merge")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.No)

        if msg.exec() == QMessageBox.StandardButton.Yes:
            try:
                data = {
                    'source_branch': source_branch,
                    'target_branch': target_branch
                }
                response = requests.post(f"{SERVER_URL}/merge", json=data)
                if response.status_code == 200:
                    self.show_message("Success", 
                                    f"Successfully merged '{source_branch}' into '{target_branch}'")
                    self.refresh_repo()
                    self.cancel_merge()  # Reset the merge UI
                else:
                    self.show_error("Merge failed")
            except Exception as e:
                self.show_error(f"Error during merge: {str(e)}")


    def show_error(self, message):
        QMessageBox.critical(self, "Error", message)

    def show_message(self, title, message):
        QMessageBox.information(self, title, message)

def main():
    app = QApplication(sys.argv)
    
    # Set fusion style for modern look
    app.setStyle("Fusion")
    
    window = GitClientGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    SERVER_URL = "https://0537-103-211-18-24.ngrok-free.app"  # Replace with your ngrok URL
    main()