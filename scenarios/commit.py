import subprocess
import time
import os
import numpy as np
import json
from datetime import datetime

# Load configuration from config.json
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

REPO_URL = config['repo_url']
ITERATIONS = config['iterations']
durations = []  # Initialize the list to store durations

# Store the base directory path
base_dir = os.getcwd()

# Check if the repository already exists
repo_path = "/tmp/repo"
if not os.path.exists(repo_path):
    # Clone the repository if it doesn't exist
    subprocess.run(["git", "clone", REPO_URL, repo_path])

# Change into the cloned directory
os.chdir(repo_path)

# Get the name of the current branch
original_branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True).stdout.strip()

# Create a new branch based on the current timestamp
timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
branch_name = f"testing-{timestamp}"
subprocess.run(["git", "checkout", "-b", branch_name])

# Create a file to make changes to
file_path = "test_file.txt"
with open(file_path, "w") as f:
    f.write("Initial content\n")

# Add the file to the staging area
subprocess.run(["git", "add", file_path])

for i in range(1, ITERATIONS + 1):
    # Make changes to the file
    with open(file_path, "a") as f:
        f.write(f"Change {i}\n")
    
    # Commit the changes
    start_time = time.time()
    commit_message = f"Commit {i}"
    commit_result = subprocess.run(["git", "commit", "-am", commit_message], capture_output=True, text=True)
    if commit_result.returncode == 0:
        # Push the changes to the remote repository
        push_result = subprocess.run(["git", "push", "origin", branch_name], capture_output=True, text=True)
        end_time = time.time()
        
        duration = (end_time - start_time) * 1000
        durations.append(duration)  # Append the duration to the list

        if push_result.returncode == 0:
            print(f"Commit and push {i} took {duration:.2f} ms and was successful")
        else:
            print(f"Failed to push commit {i} to remote: {push_result.stderr}")
    else:
        end_time = time.time()
        duration = (end_time - start_time) * 1000
        durations.append(duration)  # Append the duration to the list
        print(f"Commit {i} failed with error: {commit_result.stderr}")

# Switch back to the original branch
subprocess.run(["git", "checkout", original_branch])

# Calculate average and p95
average_duration = np.mean(durations)
p95_duration = np.percentile(durations, 95)

output = (
    f"\n---------------------------------\n"
    f"Average commit and push duration: {average_duration:.2f} ms\n"
    f"95th percentile commit and push duration: {p95_duration:.2f} ms\n"
    f"---------------------------------\n"
)

# Print the results to the console
print(output)

# Change back to the base directory
os.chdir(base_dir)

# Append the results to the results.txt file
print("Writing results to results.txt")
with open("results.txt", "a") as file:
    file.write(output)
print("Results written to results.txt")

# Cleanup branches locally and on remote
os.chdir(repo_path)
# Delete the branch locally
subprocess.run(["git", "branch", "-D", branch_name])
# Delete the branch on the remote
subprocess.run(["git", "push", "origin", "--delete", branch_name])