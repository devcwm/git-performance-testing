import subprocess
import time
import os
import numpy as np
import json
from datetime import datetime
import requests

# Load configuration from config.json
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

REPO_URL = config['repo_url']
ITERATIONS = config['iterations']
GITHUB_TOKEN = config['github_token']
REPO_OWNER = config['repo_owner']
REPO_NAME = config['repo_name']
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

timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

# Get the name of the current branch
original_branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True).stdout.strip()

# Section 1: Create Branches and Make Commits
for i in range(1, ITERATIONS + 1):
    # Create a new branch based on the current timestamp and iteration number
    branch_name = f"testing-{timestamp}-{i}"
    subprocess.run(["git", "checkout", "-b", branch_name])

    # Create a file to make changes to
    file_path = f"test_file_{i}.txt"
    with open(file_path, "w") as f:
        f.write(f"Initial content for iteration {i}\n")

    # Add the file to the staging area
    subprocess.run(["git", "add", file_path])

    # Commit the changes
    commit_message = f"Commit {i}"
    commit_result = subprocess.run(["git", "commit", "-m", commit_message], capture_output=True, text=True)
    if commit_result.returncode == 0:
        # Push the changes to the remote repository
        push_result = subprocess.run(["git", "push", "origin", branch_name], capture_output=True, text=True)
        if push_result.returncode == 0:
            print(f"Branch and commit {i} created and pushed successfully")
        else:
            print(f"Failed to push commit {i} to remote: {push_result.stderr}")
    else:
        print(f"Commit {i} failed with error: {commit_result.stderr}")

    # Switch back to the original branch
    subprocess.run(["git", "checkout", original_branch])

# Create Pull Requests and Calculate Durations
for i in range(1, ITERATIONS + 1):
    # Create a new branch name based on the current timestamp and iteration number
    branch_name = f"testing-{timestamp}-{i}"

    # Create a pull request
    start_time = time.time()
    pr_data = {
        "title": f"Test PR {i}",
        "head": branch_name,
        "base": original_branch,
        "body": f"This is a test pull request {i}"
    }
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    pr_response = requests.post(
        f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/pulls",
        json=pr_data,
        headers=headers
    )
    end_time = time.time()

    duration = (end_time - start_time) * 1000
    durations.append(duration)  # Append the duration to the list

    if pr_response.status_code == 201:
        pr_number = pr_response.json()['number']
        print(f"PR creation {i} took {duration:.2f} ms and was successful")
    else:
        print(f"Failed to create PR {i}: {pr_response.json()}")

# Calculate average and p95
average_duration = np.mean(durations)
p95_duration = np.percentile(durations, 95)

output = (
    f"\n---------------------------------\n"
    f"Average PR creation duration: {average_duration:.2f} ms\n"
    f"95th percentile PR creation duration: {p95_duration:.2f} ms\n"
    f"---------------------------------\n"
)

# Print the results to the console
print(output)

# Append the results to the results.txt file
print("Writing results to results.txt")
with open("results.txt", "a") as file:
    file.write(output)
print("Results written to results.txt")

# Section 3: Cleanup Pull Requests and Branches
os.chdir(repo_path)
# Get the list of pull requests
headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}
pr_response = requests.get(
    f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/pulls?state=open",
    headers=headers
)
if pr_response.status_code == 200:
    prs = pr_response.json()
    for pr in prs:
        pr_number = pr['number']
        branch_name = pr['head']['ref']
        # Close the pull request
        requests.patch(
            f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/pulls/{pr_number}",
            json={"state": "closed"},
            headers=headers
        )
        # Delete the branch on the remote
        subprocess.run(["git", "push", "origin", "--delete", branch_name])

# Delete the branches locally
for i in range(1, ITERATIONS + 1):
    branch_name = f"testing-{timestamp}-{i}"
    subprocess.run(["git", "branch", "-D", branch_name])

# Change back to the base directory
os.chdir(base_dir)