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
durations = []  # Initialize the list to store durations for tag creation and push
deletion_durations = []  # Initialize the list to store durations for tag deletion
fetch_durations = []  # Initialize the list to store durations for tag fetch

# Store the base directory path
base_dir = os.getcwd()

# Check if the repository already exists
repo_path = "/tmp/repo"
if not os.path.exists(repo_path):
    # Clone the repository if it doesn't exist
    subprocess.run(["git", "clone", REPO_URL, repo_path])

# Change into the cloned directory
os.chdir(repo_path)

for i in range(1, ITERATIONS + 1):
    # Create a new tag based on the current timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    tag_name = f"tag-{timestamp}-{i}"
    
    result = subprocess.run(["git", "tag", tag_name], capture_output=True, text=True)
    start_time = time.time()
    if result.returncode == 0:
        # Push the new tag to the remote repository
        push_result = subprocess.run(["git", "push", "origin", tag_name], capture_output=True, text=True)
        end_time = time.time()
        
        duration = (end_time - start_time) * 1000
        durations.append(duration)  # Append the duration to the list

        if push_result.returncode == 0:
            print(f"Tag creation and push {i} took {duration:.2f} ms and was successful")
        else:
            print(f"Failed to push tag {tag_name} to remote: {push_result.stderr}")
    else:
        end_time = time.time()
        duration = (end_time - start_time) * 1000
        durations.append(duration)  # Append the duration to the list
        print(f"Tag creation {i} failed with error: {result.stderr}")

# Calculate average and p95 for tag creation and push
average_duration = np.mean(durations)
p95_duration = np.percentile(durations, 95)

output = (
    f"\n---------------------------------\n"
    f"Average tag creation and push duration: {average_duration:.2f} ms\n"
    f"95th percentile tag creation and push duration: {p95_duration:.2f} ms\n"
    f"---------------------------------\n"
)

# Print the results to the console
print(output)

# Cleanup tags locally and on remote
os.chdir(repo_path)
tags = subprocess.run(["git", "tag"], capture_output=True, text=True).stdout.splitlines()
for tag in tags:
    tag = tag.strip()
    if tag.startswith("tag-"):
        # Measure the time taken to delete the tag locally
        start_time = time.time()
        subprocess.run(["git", "tag", "-d", tag])
        end_time = time.time()
        local_deletion_duration = (end_time - start_time) * 1000
        
        # Measure the time taken to delete the tag on the remote
        start_time = time.time()
        subprocess.run(["git", "push", "origin", "--delete", tag])
        end_time = time.time()
        remote_deletion_duration = (end_time - start_time) * 1000
        deletion_durations.append(remote_deletion_duration)

# Calculate average and p95 for tag deletion
average_deletion_duration = np.mean(deletion_durations)
p95_deletion_duration = np.percentile(deletion_durations, 95)

deletion_output = (
    f"\n---------------------------------\n"
    f"Average tag deletion duration: {average_deletion_duration:.2f} ms\n"
    f"95th percentile tag deletion duration: {p95_deletion_duration:.2f} ms\n"
    f"---------------------------------\n"
)

# Print the results to the console
print(deletion_output)

# Change back to the base directory
os.chdir(base_dir)

# Remove all tags locally and fetch all tags from remote

# Fetch all tags from remote multiple times
for i in range(1, ITERATIONS + 1):
    # Remove all tags locally before each fetch
    tags = subprocess.run(["git", "tag"], capture_output=True, text=True).stdout.splitlines()
    for tag in tags:
        tag = tag.strip()
        subprocess.run(["git", "tag", "-d", tag])

    start_time = time.time()
    subprocess.run(["git", "fetch", "--tags"])
    end_time = time.time()
    fetch_duration = (end_time - start_time) * 1000
    fetch_durations.append(fetch_duration)
    print(f"Tag fetch {i} took {fetch_duration:.2f} ms")

# Calculate average and p95 for tag fetch
average_fetch_duration = np.mean(fetch_durations)
p95_fetch_duration = np.percentile(fetch_durations, 95)

fetch_output = (
    f"\n---------------------------------\n"
    f"Average tag fetch duration: {average_fetch_duration:.2f} ms\n"
    f"95th percentile tag fetch duration: {p95_fetch_duration:.2f} ms\n"
    f"---------------------------------\n"
)

# Print the results to the console
print(fetch_output)


# Append the creation and deletion results to the results.txt file
print("Writing Tag results to results.txt")
with open("results.txt", "a") as file:
    file.write(output)
    file.write(deletion_output)
    file.write(fetch_output)
print("Tag results written to results.txt")