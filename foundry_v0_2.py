import os
import requests
import base64
import yaml

# === Load secrets from GitHub Actions ===
GITHUB_TOKEN = os.environ['FOUNDRY_TOKEN_PERSONAL']
USERNAME = os.environ['FOUNDRY_USERNAME']

if USERNAME != "darbybailey":
    raise Exception("❌ Unauthorized user. Only darbybailey can run this workflow. Please copy this to your own GitHub account, create your token and username to run in your own account")


# === Load the architecture spec ===
with open("spec.yaml", "r") as f:
    config = yaml.safe_load(f)

project_name = config["project_name"]
folders = config.get("folders", [])
files = config.get("files", [])
options = config.get("options", {})

# === Create the new repo via GitHub API ===
headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}
repo_data = {
    "name": project_name,
    "private": options.get("visibility", "public") != "public",
    "auto_init": True
}
res = requests.post("https://api.github.com/user/repos", headers=headers, json=repo_data)
if res.status_code != 201:
    raise Exception(f"❌ Repo creation failed: {res.text}")
print(f"✅ Repo created: https://github.com/{USERNAME}/{project_name}")

import shutil

# === Clean up any old run ===
if os.path.exists(project_name):
    shutil.rmtree(project_name)

# === Create folders and files locally ===
os.makedirs(project_name, exist_ok=True)
os.chdir(project_name)

def create_nested(folder):
    parts = folder.strip("/").split("/")
    path = ""
    for part in parts:
        path = os.path.join(path, part)
        os.makedirs(path, exist_ok=True)

for folder in folders:
    if isinstance(folder, str):
        create_nested(folder)
    elif isinstance(folder, dict):
        for root, subs in folder.items():
            for sub in subs:
                create_nested(f"{root}/{sub}")

for file in files:
    with open(file, "w") as f:
        f.write("")

# === Push files to new repo ===
def push_file(path, content, repo):
    url = f"https://api.github.com/repos/{USERNAME}/{repo}/contents/{path}"
    encoded = base64.b64encode(content.encode()).decode()
    data = {
        "message": f"Add {path}",
        "content": encoded
    }
    r = requests.put(url, headers=headers, json=data)
    if r.status_code not in [201, 200]:
        print(f"⚠️ Failed to push {path}: {r.text}")

# Walk and push all files
for root, dirs, files in os.walk("."):
    for file in files:
        filepath = os.path.join(root, file)
        if ".git" in filepath:
            continue
        with open(filepath, "r") as f:
            content = f.read()
        repo_path = filepath.replace("./", "")
        push_file(repo_path, content, project_name)

import shutil

# === Final step: Cleanup the local folder ===
os.chdir("..")
shutil.rmtree(project_name)
print(f"🧹 Cleaned up local project folder: {project_name}")
