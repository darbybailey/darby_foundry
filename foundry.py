import os
import yaml

# === 1. Load the blueprint spec ===
with open("spec.yaml", "r") as f:
    config = yaml.safe_load(f)

project_name = config["project_name"]
folders = config.get("folders", [])
files = config.get("files", [])
options = config.get("options", {})

# === 2. Create base project folder ===
os.makedirs(project_name, exist_ok=True)
os.chdir(project_name)

# === 3. Create folders recursively ===
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

# === 4. Create files ===
for file in files:
    with open(file, "w") as f:
        f.write("")

# === 5. Init Git if enabled ===
if options.get("git_init", False):
    os.system("git init")
    os.system("touch .gitignore")

print(f"✅ Project '{project_name}' created.")
