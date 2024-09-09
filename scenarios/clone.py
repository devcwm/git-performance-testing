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

for i in range(1, ITERATIONS + 1):
    start_time = time.time()
    subprocess.run(["git", "clone", REPO_URL, f"/tmp/repo-{i}"])
    end_time = time.time()
    duration = (end_time - start_time) * 1000
    durations.append(duration)  # Append the duration to the list
    print(f"Clone {i} took {duration:.2f} ms")
    os.system(f"rm -rf /tmp/repo-{i}")

# Calculate average and p95
average_duration = np.mean(durations)
p95_duration = np.percentile(durations, 95)

output = (
    f"\n---------------------------------\n"
    f"Average clone duration: {average_duration:.2f} ms\n"
    f"95th percentile clone duration: {p95_duration:.2f} ms\n"
    f"---------------------------------\n"
)

# Print the results to the console
print(output)

# Append the results to the results.txt file
print("Writing results to results.txt")
with open("results.txt", "a") as file:
    file.write(output)