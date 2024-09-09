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

for i in range(1, ITERATIONS + 1):
    # Create a new branch based on the current timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    branch_name = f"testing-{timestamp}-{i}"
    
    start_time = time.time()
    result = subprocess.run(["git", "checkout", "-b", branch_name], capture_output=True, text=True)
    if result.returncode == 0:
        # Push the new branch to the remote repository
        push_result = subprocess.run(["git", "push", "origin", branch_name], capture_output=True, text=True)
        end_time = time.time()
        
        duration = (end_time - start_time) * 1000
        durations.append(duration)  # Append the duration to the list

        if push_result.returncode == 0:
            print(f"Branch creation and push {i} took {duration:.2f} ms and was successful")
        else:
            print(f"Failed to push branch {branch_name} to remote: {push_result.stderr}")
    else:
        end_time = time.time()
        duration = (end_time - start_time) * 1000
        durations.append(duration)  # Append the duration to the list
        print(f"Branch creation {i} failed with error: {result.stderr}")

# Switch back to the original branch
subprocess.run(["git", "checkout", original_branch])

# Calculate average and p95
average_duration = np.mean(durations)
p95_duration = np.percentile(durations, 95)

output = (
    f"\n---------------------------------\n"
    f"Average branch creation and push duration: {average_duration:.2f} ms\n"
    f"95th percentile branch creation and push duration: {p95_duration:.2f} ms\n"
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
branches = subprocess.run(["git", "branch"], capture_output=True, text=True).stdout.splitlines()
for branch in branches:
    branch = branch.strip()
    if branch.startswith("testing-"):
        # Delete the branch locally
        subprocess.run(["git", "branch", "-D", branch])
        # Delete the branch on the remote
        subprocess.run(["git", "push", "origin", "--delete", branch])