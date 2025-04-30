# Foundry

**A symbolic scaffolding engine that builds fully structured GitHub repositories from natural language or YAML specs.**

This repo is the interface and engine. Paste your architecture, generate a new repo, and manifest your next build.

---

## Usage

1. Open the `foundry.py` file
2. Paste in your architecture spec (YAML or plain text)
3. Run the script locally to create the folder structure
4. Push it to a new GitHub repo manually (until API is wired in)

GitHub-native UI and full automation coming soon.

---

## Example Input

```yaml
project_name: signal-mapper
folders:
  - core/
    - processor/
    - entropy/
  - interface/
    - voice/
files:
  - README.md
  - .env
  - help.md
options:
  license: MIT
  git_init: true
