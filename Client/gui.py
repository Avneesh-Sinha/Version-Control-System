import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QLineEdit, QTextEdit, 
                           QLabel, QComboBox, QFileDialog, QMessageBox, 
                           QListWidget, QTabWidget, QSplitter)
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

        # Merge Tab
        merge_tab = QWidget()
        merge_layout = QVBoxLayout(merge_tab)

        # Merge controls
        merge_form = QHBoxLayout()
        self.source_branch_combo = QComboBox()
        self.target_branch_combo = QComboBox()
        merge_btn = QPushButton("Merge Branches")
        merge_btn.clicked.connect(self.merge_branches)
        
        merge_form.addWidget(QLabel("Source:"))
        merge_form.addWidget(self.source_branch_combo)
        merge_form.addWidget(QLabel("Target:"))
        merge_form.addWidget(self.target_branch_combo)
        merge_form.addWidget(merge_btn)
        merge_form.addStretch()
        merge_layout.addLayout(merge_form)

        # Add tabs to tab widget
        tab_widget.addTab(repo_tab, "Repository")
        tab_widget.addTab(merge_tab, "Merge")

        # Initialize data
        self.refresh_repo()
        self.file_list.itemClicked.connect(self.show_file_content)

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
                self.show_message("Success", "Changes pulled successfully")
                self.refresh_files()
            else:
                self.show_error("Failed to pull changes")
        except Exception as e:
            self.show_error(f"Error pulling changes: {str(e)}")

    def push_changes(self):
        current_branch = self.branch_combo.currentText()
        if not current_branch:
            self.show_error("Please select a branch")
            return

        content = self.content_edit.toPlainText()
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            self.show_error("Please select a file")
            return

        filename = selected_items[0].text()
        try:
            data = {
                'filename': filename,
                'content': content,
                'branch': current_branch
            }
            response = requests.post(f"{SERVER_URL}/push", json=data)
            if response.status_code == 200:
                self.show_message("Success", "Changes pushed successfully")
                self.refresh_files()
            else:
                self.show_error("Failed to push changes")
        except Exception as e:
            self.show_error(f"Error pushing changes: {str(e)}")

    def merge_branches(self):
        source_branch = self.source_branch_combo.currentText()
        target_branch = self.target_branch_combo.currentText()
        
        if source_branch == target_branch:
            self.show_error("Source and target branches must be different")
            return

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