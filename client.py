from vcs import VCS

# Remote server URL
remote_url = 'http://localhost:6900'

# Initialize the VCS instance
vcs = VCS()

# Push changes to the remote server
vcs.push_changes(remote_url)

# Pull changes from the remote server
vcs.pull_changes(remote_url)
