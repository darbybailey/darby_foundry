import os
import yaml
import requests

# === 1. Load the correct YAML block from spec.yaml ===
with open("spec.yaml", "r") as f:
    docs = list(yaml.safe_load_all(f))

# Look for the Foundry config block by checking for 'project_name'
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

# === 4. Create files ===
for file in files:
    with open(file, "w") as f:
        f.write("")

# === 5. Git init (optional) ===
if options.get("git_init", False):
    os.system("git init")

# === 6. Create GitHub repo if token and username are available ===
token = os.environ.get("FOUNDRY_TOKEN_PERSONAL")
username = os.environ.get("FOUNDRY_USERNAME")

if token and username:
    url = "https://api.github.com/user/repos"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "name": project_name,
        "private": options.get("visibility", "public") != "public",
        "auto_init": False,
        "license_template": options.get("license", "mit").lower()
    }

    res = requests.post(url, headers=headers, json=data)

    if res.status_code == 201:
        print(f"✅ Repo created: {res.json().get('html_url')}")
    else:
        raise Exception(f"❌ Repo creation failed: {res.text}")
else:
    print("⚠️ Skipping GitHub repo creation (missing credentials)")
