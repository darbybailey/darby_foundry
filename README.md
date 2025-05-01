🔨 Darby Foundry

A symbolic scaffolding engine that builds fully structured GitHub repositories from a single architecture spec.

Foundry creates public or private repos from YAML or text-based blueprints and powers your entire app ecosystem with traceable, intentional builds.

👉 ▶️ Run Foundry Builder

✨ How It Works

Edit the spec.yaml file

Paste in your app’s structure and set the visibility flag:

options:
  visibility: private   # or "public"

Save and commit the file

Run the workflow linked above

A new GitHub repo is created and scaffolded automatically

Foundry logs the build and self-cleans

📁 Example spec.yaml

project_name: echo-mapper
folders:
  - core/
    - ingest/
    - signal/
  - interface/
    - web/
files:
  - README.md
  - .env
  - help.md
options:
  visibility: private   # Make it public or private
  git_init: true

🧠 How Tracking Works

🔓 Public Tracker (Default)

Logs repo name, creation time, and link

(Coming soon): Adds to foundry-log.md for portfolio indexing

🔐 Private Tracker (LetHerCook)

Advanced internal tracking of:

App category, intent, audience

Time, cost, revenue, usage

Performance scoring and prioritization

Stored in your private let-her-cook repo

(Coming soon): Syncs on every build

🔐 Security

Your personal token is never committed

This engine is locked to @darbybailey and cannot be run by others

📜 License

MIT — Build your system. Own your signal.

