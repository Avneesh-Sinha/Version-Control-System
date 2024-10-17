from http.server import SimpleHTTPRequestHandler, HTTPServer
import json

commits_db = []  # Simulate the remote repository commits storage

class VCSServer(SimpleHTTPRequestHandler):
    def do_GET(self):
        """Handle pulling changes (client pulls new commits)."""
        self.send_response(200)
        self.end_headers()
        self.wfile.write(json.dumps(commits_db).encode('utf-8'))

    def do_POST(self):
        """Handle pushing changes (client sends new commits)."""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        received_commits = json.loads(post_data.decode('utf-8')).get('commits', [])
        global commits_db
        commits_db.extend(received_commits)  # Store commits in the "remote" database
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Commits received and stored.")

# Run the server
def run_server(server_class=HTTPServer, handler_class=VCSServer, port=6900):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting server on port {port}")
    httpd.serve_forever()

# Start the VCS server
if __name__ == '__main__':
    run_server()
