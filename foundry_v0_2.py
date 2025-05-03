#!/usr/bin/env python3
# Foundry v0.2 - Fixed to handle full YAML content with proper attribution

import os
import yaml
import requests
import sys
import subprocess
import time
import re

print("Starting Enhanced Foundry Builder v0.2")

try:
    # Read the spec.yaml file
    with open("spec.yaml", "r") as f:
        content = f.read()
    
    # Print the first few characters to help debug
    print(f"First 30 chars of spec.yaml: {content[:30]}")
    
    # Remove "yaml" prefix if present
    lines = content.split("\n")
    if lines[0].strip().lower() == "yaml":
        content = "\n".join(lines[1:])
        print("Removed 'yaml' header line")
    
    # Extract config section and deployment content
    config_text = content.split("---")[0].strip()
    k8s_content = content[content.find("---"):]
    
    # Parse configuration with safe_load
    config = yaml.safe_load(config_text)
    
    # Extract key info
    project_name = config.get("project_name", "gravel9-tilt")
    folders = config.get("folders", [])
    files = config.get("files", [])
    options = config.get("options", {})
    
    print(f"Project name: {project_name}")
    print(f"Folders to create: {folders}")
    print(f"Files to create: {files}")
    
    # Get GitHub credentials
    token = os.environ.get("FOUNDRY_TOKEN_PERSONAL")
    username = os.environ.get("FOUNDRY_USERNAME")
    
    if not token or not username:
        print("Missing GitHub credentials")
        sys.exit(1)
    
    # Security check
    if username != "darbybailey":
        print("Unauthorized user")
        sys.exit(1)
        
    # ENSURE USERNAME IS darby-foundry for proper attribution
    author_username = "darby-foundry"
    
    # Check for existing repository and delete if needed
    print(f"Checking for existing repository: {project_name}")
    check_url = f"https://api.github.com/repos/{username}/{project_name}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    check_res = requests.get(check_url, headers=headers)
    if check_res.status_code == 200:
        print(f"Repository exists - deleting first")
        delete_res = requests.delete(check_url, headers=headers)
        if delete_res.status_code != 204:
            print(f"Failed to delete existing repo: {delete_res.status_code} - {delete_res.text}")
            sys.exit(1)
        print(f"Existing repository deleted successfully")
        
        # Wait for GitHub to process the deletion
        print("Waiting for GitHub to process deletion...")
        time.sleep(3)
    else:
        print("No existing repository found, proceeding with creation")
    
    # Create GitHub repository
    print(f"Creating new GitHub repository: {project_name}")
    create_url = "https://api.github.com/user/repos"
    create_data = {
        "name": project_name,
        "private": options.get("visibility", "public") != "public",
        "auto_init": False
    }
    
    create_res = requests.post(create_url, headers=headers, json=create_data)
    
    if create_res.status_code != 201:
        print(f"Failed to create GitHub repository: {create_res.status_code} - {create_res.text}")
        sys.exit(1)
    
    repo_url = create_res.json().get('html_url')
    print(f"GitHub repository created: {repo_url}")
    
    # Wait for GitHub to set up the repository
    print("Waiting for GitHub to set up the repository...")
    time.sleep(2)
    
    # Create local project files
    print(f"Creating local project files")
    
    # Clean up any existing directory
    if os.path.exists(project_name):
        import shutil
        shutil.rmtree(project_name)
        print(f"Removed existing local directory: {project_name}")
    
    # Create project directory
    os.makedirs(project_name, exist_ok=True)
    os.chdir(project_name)
    print(f"Created and changed to directory: {project_name}")
    
    # Create folders
    for folder in folders:
        if isinstance(folder, str) and folder != ".":
            os.makedirs(folder, exist_ok=True)
            print(f"Created folder: {folder}")
    
    # Create files
    for file in files:
        if file == "gravel9-tilt-deployment.yaml":
            # Create deployment file with full Kubernetes content
            with open(file, "w") as f:
                f.write(k8s_content)
            
            # Debug: check file size
            file_size = os.path.getsize(file)
            print(f"Created deployment file ({file_size} bytes)")
            
            # Debug: check file content
            with open(file, "r") as f:
                first_100 = f.read(100)
            print(f"Deployment file starts with: {first_100}")
            
        elif file == "README.md":
            with open(file, "w") as f:
                f.write(f"# {project_name}\n\nResonant node for veiled patterns and sovereign memory.\n\n")
                f.write("## Components\n\n")
                f.write("- Quantum Veil\n")
                f.write("- Pattern Oracle\n")
                f.write("- Memory Totem\n")
                f.write("- Flywheel Controller\n")
                f.write("- Symbolic Signal UI\n")
            print(f"Created README file")
        else:
            with open(file, "w") as f:
                f.write("")
            print(f"Created empty file: {file}")
    
    # List files to verify
    print(f"Files created: {os.listdir('.')}")
    
    # Initialize git repository
    print("Initializing git repository")
    subprocess.run(["git", "init"], check=True)
    
    # Set git user to darby-foundry for proper attribution
    subprocess.run(["git", "config", "user.name", author_username], check=True)
    subprocess.run(["git", "config", "user.email", "foundry@example.com"], check=True)
    
    # Add and commit files
    print("Adding files to git")
    subprocess.run(["git", "add", "."], check=True)
    print("Committing files")
    subprocess.run(["git", "commit", "-m", "Initial commit from Foundry"], check=True)
    
    # Push to GitHub
    remote_url = f"https://{username}:{token}@github.com/{username}/{project_name}.git"
    print(f"Adding git remote")
    subprocess.run(["git", "remote", "add", "origin", remote_url], check=True)
    
    # Push using main branch
    print("Pushing to main branch")
    subprocess.run(["git", "branch", "-M", "main"], check=True)
    
    try:
        push_result = subprocess.run(["git", "push", "-u", "origin", "main"], 
                                   check=True, capture_output=True, text=True)
        print("Push successful")
        print(f"Push output: {push_result.stdout}")
    except subprocess.CalledProcessError as e:
        print(f"Push error: {e.stderr}")
        sys.exit(1)
    
    print(f"Repository creation complete: https://github.com/{username}/{project_name}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
