
#!/usr/bin/env python3
# Foundry v0.2 - GitHub repo generator

import os
import yaml
import requests

# === 1. Load all YAML documents from spec.yaml ===
with open("spec.yaml", "r") as f:
    # Safe load all YAML documents
    try:
        docs = list(yaml.safe_load_all(f))
        print(f"✅ Loaded {len(docs)} YAML documents from spec.yaml")
    except Exception as e:
        print(f"❌ Failed to parse YAML: {e}")
        raise

# Look for the Foundry config block (first doc with project_name)
config = next(
    (doc for doc in docs if isinstance(doc, dict) and "project_name" in doc),
    None
)

if config is None:
    raise ValueError("No Foundry config found in spec.yaml.")

project_name = config["project_name"]
folders = config.get("folders", [])
files = config.get("files", [])
options = config.get("options", {})

print(f"✅ Found project configuration: {project_name}")

# === 2. Create base project folder ===
os.makedirs(project_name, exist_ok=True)
os.chdir(project_name)
print(f"✅ Created project directory: {project_name}")

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
# For the deployment file, include all YAML docs except the config one
k8s_docs = [doc for doc in docs if doc != config and doc is not None]

for file in files:
    try:
        if file == "gravel9-tilt-deployment.yaml":
            with open(file, "w") as f:
                for i, doc in enumerate(k8s_docs):
                    yaml.dump(doc, f, default_flow_style=False)
                    if i < len(k8s_docs) - 1:
                        f.write("\n---\n")
            print(f"✅ Created deployment file with {len(k8s_docs)} K8s resources")
        else:
            # For README.md, create a simple content
            if file == "README.md":
                with open(file, "w") as f:
                    f.write(f"# {project_name}\n\nResonant node for veiled patterns and sovereign memory.")
                print(f"✅ Created README file")
            else:
                # Create empty files for other entries
                with open(file, "w") as f:
                    f.write("")
                print(f"✅ Created empty file: {file}")
    except Exception as e:
        print(f"❌ Failed to create file {file}: {e}")

# === 5. Git init (optional) ===
if options.get("git_init", False):
    try:
        os.system("git init")
        os.system("git config user.name 'Foundry Bot'")
        os.system("git config user.email 'foundry@example.com'")
        os.system("git add .")
        os.system("git commit -m 'Initial commit from Foundry'")
        print("✅ Initialized git repository and committed files")
    except Exception as e:
        print(f"❌ Git operations failed: {e}")

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
        print(f"✅ Created GitHub repository: {repo_url}")
        
        # Push to GitHub
        remote_url = f"https://{username}:{token}@github.com/{username}/{project_name}.git"
        os.system(f"git remote add origin {remote_url}")
        
        # Try both main and master branch names
        push_result = os.system("git push -u origin main")
        if push_result != 0:
            os.system("git branch -M main")  # Rename master to main if needed
            push_result = os.system("git push -u origin main")
            
        if push_result == 0:
            print("✅ Successfully pushed code to GitHub")
        else:
            # Try with master branch name as fallback
            push_result = os.system("git push -u origin master")
            if push_result == 0:
                print("✅ Successfully pushed code to GitHub using master branch")
            else:
                print("⚠️ Failed to push code to GitHub")
    else:
        print(f"❌ Failed to create GitHub repository: {res.status_code} - {res.text}")
else:
    print("⚠️ Skipping GitHub operations (missing credentials)")

print(f"✅ Foundry build complete for {project_name}!")