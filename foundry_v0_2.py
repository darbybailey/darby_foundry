#!/usr/bin/env python3
# Foundry v0.2 - Fixed version with enhanced GitHub repo creation

import os
import yaml
import requests
import sys
import time
import subprocess

try:
    print("Starting Foundry v0.2...")
    
    # Read the file and remove the erroneous "yaml" line
    with open("spec.yaml", "r") as f:
        content = f.read()
    
    # Remove the first line if it just contains "yaml"
    lines = content.split("\n")
    if lines[0].strip().lower() == "yaml":
        content = "\n".join(lines[1:])
        print("Removed 'yaml' header line")
    
    # Split by document separator
    parts = content.split("---")
    config_text = parts[0].strip()
    
    # Parse the configuration section
    config = yaml.safe_load(config_text)
    
    # Extract basic info
    project_name = config["project_name"]
    folders = config.get("folders", [])
    files = config.get("files", [])
    options = config.get("options", {})
    
    print(f"Successfully parsed config for project: {project_name}")
    
    # Create project folder
    os.makedirs(project_name, exist_ok=True)
    os.chdir(project_name)
    print(f"Created and entered directory: {project_name}")
    
    # Create folders
    for folder in folders:
        if isinstance(folder, str) and folder != ".":
            os.makedirs(folder, exist_ok=True)
            print(f"Created folder: {folder}")
    
    # Create files
    for file in files:
        if file == "gravel9-tilt-deployment.yaml":
            # Join all subsequent YAML docs
            k8s_content = "\n---\n".join(parts[1:])
            with open(file, "w") as f:
                f.write(k8s_content)
            print(f"Created deployment file: {file}")
        elif file == "README.md":
            with open(file, "w") as f:
                f.write(f"# {project_name}\n\nResonant node for veiled patterns and sovereign memory.")
            print(f"Created README file: {file}")
        else:
            with open(file, "w") as f:
                f.write("")
            print(f"Created empty file: {file}")
    
    # Git init
    if options.get("git_init", False):
        print("Initializing git repository...")
        try:
            subprocess.run(["git", "init"], check=True)
            subprocess.run(["git", "config", "user.name", "Foundry Bot"], check=True)
            subprocess.run(["git", "config", "user.email", "foundry@example.com"], check=True)
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", "Initial commit from Foundry"], check=True)
            print("Git repository initialized and files committed")
        except subprocess.CalledProcessError as e:
            print(f"Git initialization error: {e}")
    
    # Create GitHub repo
    token = os.environ.get("FOUNDRY_TOKEN_PERSONAL")
    username = os.environ.get("FOUNDRY_USERNAME")
    
    if not token or not username:
        print("❌ Missing GitHub credentials. Set FOUNDRY_TOKEN_PERSONAL and FOUNDRY_USERNAME in secrets.")
        sys.exit(1)
    
    print(f"Starting GitHub operations with user: {username}")
    
    # Security check - only allow authorized users
    if username != "darbybailey":
        print("❌ Unauthorized user.")
        sys.exit(1)
    
    # Create GitHub repository
    url = "https://api.github.com/user/repos"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "name": project_name,
        "private": options.get("visibility", "public") != "public",
        "auto_init": False
    }
    
    print(f"Creating GitHub repository: {project_name}")
    res = requests.post(url, headers=headers, json=data)
    
    if res.status_code == 201:
        repo_url = res.json().get('html_url')
        print(f"✅ GitHub repository created: {repo_url}")
        
        # Wait a moment for GitHub to set up the repo
        print("Waiting for GitHub to set up the repository...")
        time.sleep(2)
        
        # Push to GitHub
        try:
            remote_url = f"https://{username}:{token}@github.com/{username}/{project_name}.git"
            print(f"Adding remote: github.com/{username}/{project_name}.git")
            subprocess.run(["git", "remote", "add", "origin", remote_url], check=True)
            
            # Try pushing with main branch first
            try:
                print("Attempting to push to main branch...")
                subprocess.run(["git", "branch", "-M", "main"], check=True)
                subprocess.run(["git", "push", "-u", "origin", "main"], check=True)
                print("✅ Code pushed to GitHub main branch")
            except subprocess.CalledProcessError:
                print("Failed to push to main branch. Trying master branch...")
                # Try with master as fallback
                subprocess.run(["git", "branch", "-M", "master"], check=True)
                subprocess.run(["git", "push", "-u", "origin", "master"], check=True)
                print("✅ Code pushed to GitHub master branch")
        except subprocess.CalledProcessError as e:
            print(f"❌ GitHub push failed: {e}")
            # Show git status for debugging
            print("Git status:")
            subprocess.run(["git", "status"])
            print("Git remote -v:")
            subprocess.run(["git", "remote", "-v"])
    else:
        print(f"❌ GitHub repository creation failed: {res.status_code}")
        print(f"Response: {res.text}")
    
    print(f"✅ Foundry build complete for {project_name}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)