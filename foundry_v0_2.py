#!/usr/bin/env python3
# Foundry v0.2 - GitHub repo generator
# Handles complex YAML with K8s specifications

import os
import yaml
import requests
import re

# === Setup custom YAML processing ===
def custom_yaml_loader():
    with open("spec.yaml", "r") as f:
        content = f.read()
    
    # First, extract the foundry config from the beginning
    config_pattern = r'^project_name:.*?(?=^---)'
    config_match = re.search(config_pattern, content, re.DOTALL | re.MULTILINE)
    
    if not config_match:
        raise ValueError("No Foundry config found in spec.yaml.")
    
    config_text = config_match.group(0)
    
    # Parse just the config section
    config = yaml.safe_load(config_text)
    
    # Extract all content after first '---' for k8s resources
    deployment_content = content[content.find('---'):]
    
    return config, deployment_content

# === 1. Load the correct YAML blocks from spec.yaml ===
config, deployment_content = custom_yaml_loader()

project_name = config["project_name"]
folders = config.get("folders", [])
files = config.get("files", [])
options = config.get("options", {})

print(f"✅ Loaded project config: {project_name}")

# === 2. Create base project folder ===
os.makedirs(project_name, exist_ok=True)
os.chdir(project_name)

# === 3. Recursively create folders ===
def create_nested(path):
    full_path = ""
    for part in path.strip("/").split("/"):
        full_path = os.path.join(full_path, part)
        os.makedirs(full_path, exist_ok=True)

for folder in folders:
    if isinstance(folder, str):
        create_nested(folder)
        print(f"✅ Created folder: {folder}")

# === 4. Create files ===
for file in files:
    if file == "gravel9-tilt-deployment.yaml":
        # Save the deployment content to the deployment file
        with open(file, "w") as f:
            f.write(deployment_content)
        print(f"✅ Created file with k8s resources: {file}")
    else:
        # Create empty files for other entries
        with open(file, "w") as f:
            f.write("")
        print(f"✅ Created empty file: {file}")

# === 5. Git init (optional) ===
if options.get("git_init", False):
    os.system("git init")
    print("✅ Initialized git repository")

# === 6. Create GitHub repo if token and username are available ===
token = os.environ.get("FOUNDRY_TOKEN_PERSONAL")
username = os.environ.get("FOUNDRY_USERNAME")

if token and username:
    # Security check - only allow authorized users
    if username != "darbybailey":
        raise Exception("❌ Unauthorized user.")
    
    url = "https://api.github.com/user/repos"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "name": project_name,
        "private": options.get("visibility", "public") != "public",
        "auto_init": False,
        "license_template": options.get("license", "mit").lower() if options.get("license", "mit").lower() in ["mit", "apache-2.0", "gpl-3.0"] else None
    }

    res = requests.post(url, headers=headers, json=data)

    if res.status_code == 201:
        print(f"✅ Repo created: {res.json().get('html_url')}")
        
        # Push to GitHub
        os.system(f"git add .")
        os.system(f"git commit -m 'Initial commit from Foundry'")
        os.system(f"git remote add origin https://{username}:{token}@github.com/{username}/{project_name}.git")
        os.system(f"git push -u origin master")
        print("✅ Code pushed to GitHub")
    else:
        raise Exception(f"❌ Repo creation failed: {res.text}")
else:
    print("⚠️ Skipping GitHub repo creation (missing credentials)")

print(f"✅ Foundry build complete for {project_name}!")