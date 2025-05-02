
#!/usr/bin/env python3
# Foundry v0.2 - Fixed to handle invalid YAML header

import os
import yaml
import requests
import sys

try:
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
    
    # Create folders
    for folder in folders:
        if isinstance(folder, str) and folder != ".":
            os.makedirs(folder, exist_ok=True)
    
    # Create files
    for file in files:
        if file == "gravel9-tilt-deployment.yaml":
            # Join all subsequent YAML docs
            k8s_content = "\n---\n".join(parts[1:])
            with open(file, "w") as f:
                f.write(k8s_content)
        elif file == "README.md":
            with open(file, "w") as f:
                f.write(f"# {project_name}\n\nResonant node for veiled patterns and sovereign memory.")
        else:
            with open(file, "w") as f:
                f.write("")
    
    # Git init
    if options.get("git_init", False):
        os.system("git init")
        os.system("git config user.name 'Foundry Bot'")
        os.system("git config user.email 'foundry@example.com'")
        os.system("git add .")
        os.system("git commit -m 'Initial commit from Foundry'")
    
    # Create GitHub repo
    token = os.environ.get("FOUNDRY_TOKEN_PERSONAL")
    username = os.environ.get("FOUNDRY_USERNAME")
    
    if token and username:
        if username != "darbybailey":
            sys.exit("Unauthorized user")
        
        url = "https://api.github.com/user/repos"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        data = {
            "name": project_name,
            "private": options.get("visibility", "public") != "public"
        }
        
        res = requests.post(url, headers=headers, json=data)
        
        if res.status_code == 201:
            remote_url = f"https://{username}:{token}@github.com/{username}/{project_name}.git"
            os.system(f"git remote add origin {remote_url}")
            os.system("git push -u origin main")
            print(f"Repository created and code pushed to GitHub")
    
    print(f"Build complete for {project_name}")
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)