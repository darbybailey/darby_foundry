
#!/usr/bin/env python3
# Foundry v0.2 - Iterative Builder with Error Correction

import os
import yaml
import requests
import sys
import subprocess
import time
import re
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('foundry')

class FoundryBuilder:
    def __init__(self):
        self.project_name = None
        self.folders = []
        self.files = []
        self.options = {}
        self.username = os.environ.get("FOUNDRY_USERNAME")
        self.token = os.environ.get("FOUNDRY_TOKEN_PERSONAL")
        self.k8s_resources = []
        
    def validate_auth(self):
        """Validate authentication credentials"""
        if not self.token or not self.username:
            logger.error("Missing GitHub credentials")
            return False
            
        if self.username != "darbybailey":
            logger.error("Unauthorized user")
            return False
            
        return True
        
    def parse_yaml(self):
        """Parse YAML with error correction"""
        try:
            # Read the spec.yaml file
            with open("spec.yaml", "r") as f:
                content = f.read()
            
            # Remove "yaml" prefix if present
            lines = content.split("\n")
            if lines[0].strip().lower() == "yaml":
                content = "\n".join(lines[1:])
                logger.info("Removed 'yaml' header line")
            
            # Manually split sections by '---'
            parts = content.split("---")
            config_text = parts[0].strip()
            self.k8s_resources = [part.strip() for part in parts[1:] if part.strip()]
            
            # Try to parse the configuration with error handling
            try:
                config = yaml.safe_load(config_text)
                if not isinstance(config, dict):
                    raise ValueError("Config section is not a valid YAML dictionary")
                
                # Extract key info
                self.project_name = config.get("project_name", "gravel9-tilt")
                self.folders = config.get("folders", [])
                self.files = config.get("files", [])
                self.options = config.get("options", {})
                
                logger.info(f"Successfully parsed config for project: {self.project_name}")
                return True
            except Exception as yaml_error:
                logger.error(f"YAML parsing error: {yaml_error}")
                
                # Try manual parsing as fallback
                config = {}
                for line in config_text.split("\n"):
                    if ":" in line and not line.strip().startswith("#"):
                        key, value = line.split(":", 1)
                        key = key.strip()
                        if key == "project_name":
                            self.project_name = value.strip()
                        elif key == "folders":
                            folder_lines = config_text.split("folders:")[1].split("files:")[0].strip().split("\n")
                            self.folders = [f.strip()[2:] for f in folder_lines if f.strip().startswith("-")]
                        elif key == "files":
                            if "options:" in config_text:
                                file_lines = config_text.split("files:")[1].split("options:")[0].strip().split("\n")
                            else:
                                file_lines = config_text.split("files:")[1].strip().split("\n")
                            self.files = [f.strip()[2:] for f in file_lines if f.strip().startswith("-")]
                
                if not self.project_name:
                    self.project_name = "gravel9-tilt"  # Default fallback
                    
                logger.info(f"Used manual parsing fallback for project: {self.project_name}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to parse spec.yaml: {e}")
            return False
    
    def check_delete_repo(self):
        """Check if repository exists and delete it if needed"""
        if not self.validate_auth():
            return False
            
        logger.info(f"Checking for existing repository: {self.project_name}")
        check_url = f"https://api.github.com/repos/{self.username}/{self.project_name}"
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        try:
            check_res = requests.get(check_url, headers=headers)
            if check_res.status_code == 200:
                logger.info(f"Repository exists - deleting first")
                delete_res = requests.delete(check_url, headers=headers)
                if delete_res.status_code != 204:
                    logger.error(f"Failed to delete existing repo: {delete_res.status_code} - {delete_res.text}")
                    return False
                logger.info(f"Existing repository deleted successfully")
                
                # Wait for GitHub to process the deletion
                logger.info("Waiting for GitHub to process deletion...")
                time.sleep(3)
            else:
                logger.info("No existing repository found, proceeding with creation")
                
            return True
        except Exception as e:
            logger.error(f"Error checking/deleting repository: {e}")
            return False
    
    def create_github_repo(self):
        """Create a new GitHub repository"""
        if not self.validate_auth():
            return False
            
        logger.info(f"Creating new GitHub repository: {self.project_name}")
        create_url = "https://api.github.com/user/repos"
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        create_data = {
            "name": self.project_name,
            "private": self.options.get("visibility", "public") != "public",
            "auto_init": False
        }
        
        try:
            create_res = requests.post(create_url, headers=headers, json=create_data)
            
            if create_res.status_code != 201:
                logger.error(f"Failed to create GitHub repository: {create_res.status_code} - {create_res.text}")
                return False
            
            repo_url = create_res.json().get('html_url')
            logger.info(f"GitHub repository created: {repo_url}")
            
            # Wait for GitHub to set up the repository
            logger.info("Waiting for GitHub to set up the repository...")
            time.sleep(2)
            
            return True
        except Exception as e:
            logger.error(f"Error creating GitHub repository: {e}")
            return False
    
    def create_project_files(self):
        """Create project directory and files"""
        try:
            logger.info(f"Creating local project files")
            
            # Clean up any existing directory first
            if os.path.exists(self.project_name):
                import shutil
                shutil.rmtree(self.project_name)
                logger.info(f"Removed existing local directory: {self.project_name}")
            
            # Create project directory
            os.makedirs(self.project_name, exist_ok=True)
            os.chdir(self.project_name)
            logger.info(f"Created and changed to directory: {self.project_name}")
            
            # Create folders recursively
            self.create_folders_recursive(self.folders)
            
            # Create files
            for file in self.files:
                self.create_file(file)
            
            # List files to verify
            logger.info(f"Files created: {os.listdir('.')}")
            return True
        except Exception as e:
            logger.error(f"Error creating project files: {e}")
            return False
    
    def create_folders_recursive(self, folders, base_path=""):
        """Create folders recursively with proper nesting"""
        for folder in folders:
            if isinstance(folder, str):
                if folder != ".":  # Skip current directory
                    folder_path = os.path.join(base_path, folder)
                    os.makedirs(folder_path, exist_ok=True)
                    logger.info(f"Created folder: {folder_path}")
    
    def create_file(self, file):
        """Create individual file with appropriate content"""
        try:
            if file == f"{self.project_name}-deployment.yaml":
                # Create the deployment file with all Kubernetes resources
                with open(file, "w") as f:
                    for i, resource in enumerate(self.k8s_resources):
                        f.write("---\n")
                        f.write(resource)
                        f.write("\n")
                logger.info(f"Created Kubernetes deployment file with {len(self.k8s_resources)} resources")
            elif file == "README.md":
                with open(file, "w") as f:
                    f.write(f"# {self.project_name}\n\nResonant node for veiled patterns and sovereign memory.\n\n")
                    f.write("## Components\n\n")
                    f.write("- Quantum Veil\n")
                    f.write("- Pattern Oracle\n")
                    f.write("- Memory Totem\n")
                    f.write("- Flywheel Controller\n")
                    f.write("- Symbolic Signal UI\n")
                logger.info(f"Created README file")
            else:
                with open(file, "w") as f:
                    f.write("")
                logger.info(f"Created empty file: {file}")
            return True
        except Exception as e:
            logger.error(f"Error creating file {file}: {e}")
            return False
    
    def init_git_and_push(self):
        """Initialize git repository and push to GitHub"""
        try:
            logger.info("Initializing git repository")
            subprocess.run(["git", "init"], check=True)
            subprocess.run(["git", "config", "user.name", "Foundry Bot"], check=True)
            subprocess.run(["git", "config", "user.email", "foundry@example.com"], check=True)
            
            # Add and commit files
            logger.info("Adding files to git")
            subprocess.run(["git", "add", "."], check=True)
            logger.info("Committing files")
            subprocess.run(["git", "commit", "-m", "Initial commit from Foundry"], check=True)
            
            # Push to GitHub
            remote_url = f"https://{self.username}:{self.token}@github.com/{self.username}/{self.project_name}.git"
            logger.info(f"Adding git remote")
            subprocess.run(["git", "remote", "add", "origin", remote_url], check=True)
            
            # Push using main branch
            logger.info("Pushing to main branch")
            subprocess.run(["git", "branch", "-M", "main"], check=True)
            try:
                subprocess.run(["git", "push", "-u", "origin", "main"], check=True)
                logger.info(f"Push successful")
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f"Push error: {e}")
                return False
        except Exception as e:
            logger.error(f"Error initializing git or pushing to GitHub: {e}")
            return False
    
    def run(self):
        """Main execution flow with error correction"""
        logger.info("Starting Foundry Builder with iterative error correction")
        
        if not self.parse_yaml():
            logger.error("Parsing YAML failed, cannot continue")
            return False
        
        if not self.check_delete_repo():
            logger.warning("Repository check/delete had issues, attempting to continue")
        
        if not self.create_github_repo():
            logger.error("Creating GitHub repository failed, cannot continue")
            return False
        
        if not self.create_project_files():
            logger.error("Creating project files failed, cannot continue")
            return False
        
        if not self.init_git_and_push():
            logger.error("Git initialization or push failed")
            return False
        
        logger.info(f"Repository creation complete: https://github.com/{self.username}/{self.project_name}")
        return True

# Execute the build process
if __name__ == "__main__":
    builder = FoundryBuilder()
    success = builder.run()
    sys.exit(0 if success else 1)