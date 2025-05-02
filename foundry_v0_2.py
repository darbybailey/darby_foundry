
#!/usr/bin/env python3
# Foundry v0.2 - Minimal debug version

import os
import yaml
import requests
import sys
import subprocess

# Print the current working directory
print(f"Current working directory: {os.getcwd()}")
print(f"Directory contents: {os.listdir('.')}")

try:
    # Read the file and fix YAML issues
    with open("spec.yaml", "r") as f:
        content = f.read()
    
    # Remove "yaml" header if present
    lines = content.split("\n")
    if lines[0].strip().lower() == "yaml":
        content = "\n".join(lines[1:])
    
    # Split by document separator
    parts = content.split("---")
    config_text = parts[0].strip()
    
    # Parse configuration with safer approach
    try:
        config = yaml.safe_load(config_text)
        print("Config parsed successfully:")
        print(config)
    except Exception as yaml_error:
        print(f"YAML parsing error: {yaml_error}")
        # Try manual parsing as fallback
        config = {}
        for line in config_text.split("\n"):
            if ":" in line and not line.strip().startswith("#"):
                key, value = line.split(":", 1)
                config[key.strip()] = value.strip()
        print("Manual parsing result:")
        print(config)
    
    # Extract basic info
    project_name = config.get("project_name", "gravel9-tilt")
    print(f"Project name: {project_name}")
    
    # Create project directory
    print(f"Creating directory: {project_name}")
    os.makedirs(project_name, exist_ok=True)
    
    # Move into project directory
    print(f"Changing to directory: {project_name}")
    os.chdir(project_name)
    
    # Create a simple file to verify operations
    print("Creating test files")
    with open("README.md", "w") as f:
        f.write(f"# {project_name}\n\nProject created by Foundry.")
    
    with open("gravel9-tilt-deployment.yaml", "w") as f:
        f.write("\n".join(parts[1:]))
    
    # List directory contents to verify
    print(f"Files created in {os.getcwd()}: {os.listdir('.')}")
    
    # Initialize git
    print("Initializing git repository")
    subprocess.run(["git", "init"], check=True)
    subprocess.run(["git", "config", "user.name", "Foundry Bot"], check=True)
    subprocess.run(["git", "config", "user.email", "foundry@example.com"], check=True)
    
    # Add and commit files
    print("Adding files to git")
    subprocess.run(["git", "add", "."], check=True)
    print("Committing files")
    subprocess.run(["git", "commit", "-m", "Initial commit from Foundry"], check=True)
    
    # Get credentials
    token = os.environ.get("FOUNDRY_TOKEN_PERSONAL")
    username = os.environ.get("FOUNDRY_USERNAME")
    
    if not token or not username:
        print("Missing GitHub credentials")
        sys.exit(1)
    
    print(f"Using GitHub credentials for user: {username}")
    
    # Create GitHub repository
    print(f"Creating GitHub repository: {project_name}")
    url = "https://api.github.com/user/repos"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "name": project_name,
        "private": False,
        "auto_init": False
    }
    
    res = requests.post(url, headers=headers, json=data)
    print(f"GitHub API response: {res.status_code}")
    
    if res.status_code == 201:
        repo_url = res.json().get('html_url')
        print(f"GitHub repository created: {repo_url}")
        
        # Push to GitHub
        remote_url = f"https://{username}:{token}@github.com/{username}/{project_name}.git"
        print(f"Adding git remote")
        subprocess.run(["git", "remote", "add", "origin", remote_url], check=True)
        
        # Try main branch
        print("Pushing to main branch")
        try:
            subprocess.run(["git", "branch", "-M", "main"], check=True)
            subprocess.run(["git", "push", "-u", "origin", "main"], check=True, 
                          stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            print(f"Push error: {e}")
            print(f"STDOUT: {e.stdout.decode() if e.stdout else 'None'}")
            print(f"STDERR: {e.stderr.decode() if e.stderr else 'None'}")
            
            # Try master branch as fallback
            print("Trying master branch instead")
            try:
                subprocess.run(["git", "branch", "-M", "master"], check=True)
                subprocess.run(["git", "push", "-u", "origin", "master"], check=True,
                             stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            except subprocess.CalledProcessError as e2:
                print(f"Master branch push error: {e2}")
                print(f"STDOUT: {e2.stdout.decode() if e2.stdout else 'None'}")
                print(f"STDERR: {e2.stderr.decode() if e2.stderr else 'None'}")
        
        print("Git push operation complete")
    else:
        print(f"GitHub repository creation failed. Response: {res.text}")
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)

print("Script completed")