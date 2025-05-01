# ⚙️ Darby Foundry — a Self-Replicating Dev Deployer

**Foundry** is a GitHub-native code scaffolding engine that creates fully structured repos from symbolic specs.  
It's the core of the Darby ecosystem — used to generate, launch, and track all app builds across domains.

This repo auto-generates:
- 🔨 Public or private GitHub repos
- 🧱 Full folder and file structures based on your custom spec
- 🧹 Self-cleaning builds
- 🧠 Optional metadata tracking (see below)

---

## ✍️ How to Use Foundry

1. Open [`spec.yaml`](spec.yaml)
2. Paste your project architecture (see example below)
3. Save and commit
4. [Run Foundry Builder →](../../actions/workflows/build.yml)
5. A new repo is created with:
   - All folders/files scaffolded
   - Pushed to your GitHub account
   - Local working directory wiped

---

## 📁 Example `spec.yaml`

### Public repo:
```yaml
project_name: kanban-scribe
folders:
  - core/
    - logic/
    - ui/
files:
  - README.md
  - .env
  - help.md
options:
  visibility: public
  license: MIT
  git_init: true


project_name: finance-mirror
folders:
  - logic/
  - dashboard/
files:
  - README.md
  - .env
  - accounts.csv
options:
  visibility: private
  git_init: true


🔐 Tracking + Privacy
Foundry currently supports two layers of tracking:

1. foundry tracks build metadata (basic, optional)
✅ Repo name, creation timestamp, visibility

Future version will log this to foundry-log.json

2. let-her-cook (private) will track full ecosystem data
💸 Estimated costs, dev time, phases

📊 Ranking, category, tags, status

💾 Stored in a secure internal repo

🧠 Why Foundry Exists
This engine gives Darby the power to:

Generate entire dev stacks from YAML specs
Track ecosystem growth
Launch symbolic systems at scale

---

## ⚠️ Security Notice

This repo includes a GitHub Action that is **locked to the original creator’s account** using a username check in `foundry_v0_2.py`.

### 🚫 Do not attempt to run workflows in this repo unless:
- You are the original owner (`darbybailey`)
- You have configured your own GitHub token + username in a fork

### ✅ Want to use Foundry?

1. **Fork this repo**
2. Go to your fork → `Settings → Secrets → Actions`
3. Add your own:
   - `FOUNDRY_TOKEN_PERSONAL` (GitHub Personal Access Token)
   - `FOUNDRY_USERNAME` (your GitHub username)
4. Update `foundry_v0_2.py` to replace `darbybailey` with your GitHub username in the locked line:
   ```python
   if USERNAME != "yourusername":
       raise Exception("❌ Unauthorized user.")
Once configured, you can safely use Foundry as your own GitHub-native scaffold generator.

License
MIT — Build your system, own your signal.
