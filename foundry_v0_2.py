
#!/usr/bin/env python3
# Foundry v0.2 - GitHub repo generator
# Handles complex YAML with K8s specifications

import os
import yaml
import requests
import re
import subprocess

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
        # Create a README with project info
        if file == "README.md":
            with open(file, "w") as f:
                f.write(f"# {project_name}\n\nResonant node for veiled patterns and sovereign memory.\n\n## Components\n\n- Quantum Veil\n- Pattern Oracle\n- Memory Totem\n- Flywheel Controller\n- Symbolic Signal UI\n\n© {2025} Proprietary - All Rights Reserved")
            print(f"✅ Created README with project info: {file}")
        else:
            # Create empty files for other entries
            with open(file, "w") as f:
                f.write("")
            print(f"✅ Created empty file: {file}")

# === 5. Git init (optional) ===
if options.get("git_init", False):
    try:
        # Initialize git repository
        subprocess.run(["git", "init"], check=True)
        print("✅ Initialized git repository")
        
        # Configure git user info for the commit
        subprocess.run(["git", "config", "user.name", "Foundry Bot"], check=True)
        subprocess.run(["git", "config", "user.email", "foundry@example.com"], check=True)
        
        # Add all files and commit
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit from Foundry"], check=True)
        print("✅ Committed files to local repository")
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Git operation failed: {e}")

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
        repo_url = res.json().get('html_url')
        print(f"✅ Repo created: {repo_url}")
        
        # Push to GitHub
        try:
            # Configure the remote
            remote_url = f"https://{username}:{token}@github.com/{username}/{project_name}.git"
            subprocess.run(["git", "remote", "add", "origin", remote_url], check=True)
            
            # Push to the remote repository
            subprocess.run(["git", "push", "-u", "origin", "master"], check=True)
            print("✅ Code pushed to GitHub successfully")
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Failed to push to GitHub: {e}")
    else:
        raise Exception(f"❌ Repo creation failed: {res.status_code} - {res.text}")
else:
    print("⚠️ Skipping GitHub repo creation (missing credentials)")

print(f"✅ Foundry build complete for {project_name}!")