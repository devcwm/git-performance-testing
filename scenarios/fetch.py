import subprocess
import time
import os
import numpy as np
import json

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

for i in range(1, ITERATIONS + 1):
    start_time = time.time()
    result = subprocess.run(["git", "fetch", "origin"], capture_output=True, text=True)
    end_time = time.time()
    duration = (end_time - start_time) * 1000
    durations.append(duration)  # Append the duration to the list

    if result.returncode == 0:
        print(f"Fetch {i} took {duration:.2f} ms and was successful")
    else:
        print(f"Fetch {i} failed with error: {result.stderr}")

# Calculate average and p95
average_duration = np.mean(durations)
p95_duration = np.percentile(durations, 95)

output = (
    f"\n---------------------------------\n"
    f"Average fetch duration: {average_duration:.2f} ms\n"
    f"95th percentile fetch duration: {p95_duration:.2f} ms\n"
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