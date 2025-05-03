#!/usr/bin/env python3
"""
Darby Foundry - Repository Builder Tool

A GitHub-native project scaffolding engine that builds full repositories from architecture specs.
The tool reads a YAML specification file and creates a complete repository structure with
necessary files, configurations, and documentation.

Usage:
    python foundry_v0_2.py --spec path/to/spec.yaml [--token GITHUB_TOKEN] [--output-dir ./output]
"""

import os
import sys
import yaml
import json
import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import requests
import base64
import logging
import time
import re
import datetime
import uuid

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("Foundry")

class FoundryError(Exception):
    """Base exception for Foundry errors"""
    pass

class RepositorySpec:
    """Represents a repository specification loaded from YAML"""
    
    def __init__(self, spec_path: str):
        """
        Load repository specification from a YAML file
        
        Args:
            spec_path: Path to the YAML specification file
        """
        self.spec_path = spec_path
        self.spec_data = self._load_spec()
        self.project_id = str(uuid.uuid4())[:8]  # Generate a unique ID for this project
        self.validate()
    
    def _load_spec(self) -> Dict[str, Any]:
        """
        Load the specification from YAML
        
        Returns:
            Dictionary containing the specification data
        
        Raises:
            FoundryError if the file cannot be loaded or parsed
        """
        try:
            with open(self.spec_path, 'r') as f:
                return yaml.safe_load(f)
        except (yaml.YAMLError, FileNotFoundError) as e:
            raise FoundryError(f"Failed to load specification from {self.spec_path}: {e}")
    
    def validate(self) -> None:
        """
        Validate the specification for required fields
        
        Raises:
            FoundryError if validation fails
        """
        # Minimal validation to ensure we can access basic properties
        # The spec format is flexible and can vary, so we only check essential fields
        if not isinstance(self.spec_data, dict):
            raise FoundryError(f"Specification must be a dictionary/mapping")
        
        # Check for repository section
        if 'repository' not in self.spec_data:
            raise FoundryError(f"Missing required 'repository' section in specification")
        
        # Check required repository fields
        repo_section = self.spec_data['repository']
        if not isinstance(repo_section, dict):
            raise FoundryError(f"Repository section must be a dictionary/mapping")
        
        if 'name' not in repo_section:
            raise FoundryError(f"Missing required 'name' field in repository section")
        
        logger.info(f"Specification validated successfully")
    
    def get_value(self, path: str, default: Any = None) -> Any:
        """
        Get a value from the specification using a dot-notation path
        
        Args:
            path: Dot-notation path to the value (e.g., 'repository.name')
            default: Default value to return if the path doesn't exist
            
        Returns:
            The value at the specified path, or the default value if it doesn't exist
        """
        parts = path.split('.')
        value = self.spec_data
        
        try:
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return default
            return value
        except (KeyError, TypeError):
            return default
    
    @property
    def repo_name(self) -> str:
        """Get the repository name"""
        return self.get_value('repository.name', '')
    
    @property
    def repo_description(self) -> str:
        """Get the repository description"""
        return self.get_value('repository.description', '')
    
    @property
    def repo_visibility(self) -> str:
        """Get the repository visibility"""
        return self.get_value('repository.visibility', 'public')
    
    @property
    def repo_license(self) -> str:
        """Get the repository license"""
        return self.get_value('repository.license', 'MIT')
    
    @property
    def repo_topics(self) -> List[str]:
        """Get the repository topics"""
        topics = self.get_value('repository.topics', [])
        return topics if isinstance(topics, list) else []
    
    @property
    def components(self) -> List[Dict[str, Any]]:
        """Get the repository components"""
        components = self.get_value('structure.components', [])
        return components if isinstance(components, list) else []
    
    @property
    def features(self) -> List[Dict[str, Any]]:
        """Get the repository features"""
        features = self.get_value('features', [])
        return features if isinstance(features, list) else []


class FileGenerator:
    """Generates files based on repository specifications"""
    
    def __init__(self, spec: RepositorySpec, output_dir: str):
        """
        Initialize the file generator
        
        Args:
            spec: Repository specification
            output_dir: Directory to output the files
        """
        self.spec = spec
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_all(self) -> None:
        """Generate all files specified in the repository specification"""
        logger.info(f"Generating files in {self.output_dir}")
        
        # Generate component files
        for component in self.spec.components:
            self._generate_component_files(component)
        
        # Generate README.md
        self._generate_readme()
        
        # Generate LICENSE file
        self._generate_license()
        
        # Generate .gitignore
        self._generate_gitignore()
        
        # Generate any special files specified in the spec
        self._generate_special_files()
        
        logger.info(f"All files generated successfully")
    
    def _generate_component_files(self, component: Dict[str, Any]) -> None:
        """
        Generate files for a component
        
        Args:
            component: Component specification
        """
        name = component.get('name', 'unknown')
        files = component.get('files', [])
        
        logger.info(f"Generating files for component: {name}")
        
        for file_path in files:
            full_path = os.path.join(self.output_dir, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # Check if the file already exists
            if os.path.exists(full_path):
                logger.info(f"File already exists: {file_path}")
                continue
            
            # Generate appropriate content based on file extension
            content = self._generate_file_content(file_path, component)
            
            with open(full_path, 'w') as f:
                f.write(content)
            
            logger.info(f"Generated file: {file_path}")
    
    def _generate_file_content(self, file_path: str, component: Dict[str, Any]) -> str:
        """
        Generate content for a file based on its extension and component
        
        Args:
            file_path: Path to the file
            component: Component specification
            
        Returns:
            Generated content for the file
        """
        ext = os.path.splitext(file_path)[1].lower()
        name = component.get('name', 'unknown')
        language = component.get('language', 'unknown')
        description = component.get('description', '')
        
        # Get base filename without path or extension
        basename = os.path.basename(file_path)
        filename_without_ext = os.path.splitext(basename)[0]
        
        # Current date for file headers
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Generate content based on file extension
        if ext == '.py':
            return self._generate_python_file(file_path, name, description)
        elif ext == '.md':
            return self._generate_markdown_file(file_path, name, description)
        elif ext == '.tsx' or ext == '.ts' or ext == '.js':
            return self._generate_typescript_file(file_path, name, description)
        elif ext == '.json':
            return self._generate_json_file(file_path)
        elif ext == '.yml' or ext == '.yaml':
            return self._generate_yaml_file(file_path)
        else:
            # Generic file content
            return f"# {os.path.basename(file_path)}\n# Generated by Darby Foundry on {current_date}\n# Component: {name}\n# Description: {description}\n\n# TODO: Implement {filename_without_ext} functionality\n"
    
    def _generate_python_file(self, file_path: str, component_name: str, description: str) -> str:
        """Generate content for a Python file"""
        basename = os.path.basename(file_path)
        filename_without_ext = os.path.splitext(basename)[0]
        
        # Handle __init__.py files specially
        if basename == '__init__.py':
            parent_dir = os.path.basename(os.path.dirname(file_path))
            return f'''"""
{parent_dir} module for {self.spec.repo_name}
"""

__version__ = "0.1.0"
'''
        
        # For regular Python files
        class_name = ''.join(word.capitalize() for word in filename_without_ext.split('_'))
        
        return f'''"""
{filename_without_ext}.py - {description}

Part of the {component_name} component in {self.spec.repo_name}
"""

from typing import Dict, List, Any, Optional


class {class_name}:
    """
    {description}
    """
    
    def __init__(self):
        """Initialize the {class_name}"""
        pass
    
    def run(self) -> None:
        """Run the main functionality"""
        pass


# Example usage
if __name__ == "__main__":
    instance = {class_name}()
    instance.run()
'''
    
    def _generate_markdown_file(self, file_path: str, component_name: str, description: str) -> str:
        """Generate content for a Markdown file"""
        basename = os.path.basename(file_path)
        filename_without_ext = os.path.splitext(basename)[0]
        title = ' '.join(word.capitalize() for word in filename_without_ext.split('_'))
        
        # Handle index.md specially
        if basename == 'index.md':
            return f'''# {self.spec.repo_name}

{self.spec.repo_description}

## Overview

This documentation covers the {self.spec.repo_name} project, a {description}.

## Components

{self._generate_components_list_markdown()}

## Features

{self._generate_features_list_markdown()}

## Getting Started

TODO: Add getting started instructions
'''
        
        # For regular markdown files
        return f'''# {title}

{description}

## Overview

TODO: Add overview for {title}

## Usage

TODO: Add usage instructions

## Reference

TODO: Add reference documentation
'''
    
    def _generate_typescript_file(self, file_path: str, component_name: str, description: str) -> str:
        """Generate content for a TypeScript/React file"""
        basename = os.path.basename(file_path)
        filename_without_ext = os.path.splitext(basename)[0]
        component_name = ''.join(word.capitalize() for word in filename_without_ext.split('_'))
        
        return f'''/**
 * {component_name} Component
 * 
 * {description}
 */

import React, {{ useState, useEffect }} from 'react';

interface {component_name}Props {{
  // TODO: Define props
}}

/**
 * {component_name} - {description}
 */
const {component_name}: React.FC<{component_name}Props> = (props) => {{
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {{
    // Component mount effect
    setLoading(false);
    
    return () => {{
      // Component unmount cleanup
    }};
  }}, []);

  return (
    <div className="{filename_without_ext}-container">
      <h2>{component_name}</h2>
      {{loading ? (
        <div>Loading...</div>
      ) : (
        <div>
          {/* TODO: Implement component content */}
          <p>Component content goes here</p>
        </div>
      )}}
    </div>
  );
}};

export default {component_name};
'''
    
    def _generate_json_file(self, file_path: str) -> str:
        """Generate content for a JSON file"""
        basename = os.path.basename(file_path)
        
        # Create a simple JSON structure
        data = {
            "name": f"{self.spec.repo_name}",
            "description": f"{self.spec.repo_description}",
            "version": "0.1.0",
            "generated": True,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        return json.dumps(data, indent=2)
    
    def _generate_yaml_file(self, file_path: str) -> str:
        """Generate content for a YAML file"""
        basename = os.path.basename(file_path)
        
        # Create a simple YAML structure
        content = f'''# {basename}
# Generated by Darby Foundry

name: {self.spec.repo_name}
description: {self.spec.repo_description}
version: 0.1.0
generated: true
timestamp: {datetime.datetime.now().isoformat()}
'''
        return content
    
    def _generate_readme(self) -> None:
        """Generate README.md file"""
        readme_path = os.path.join(self.output_dir, "README.md")
        
        content = f'''# {self.spec.repo_name}

{self.spec.repo_description}

## Overview

TODO: Add project overview

## Features

{self._generate_features_list_markdown()}

## Installation

```bash
# TODO: Add installation instructions
```

## Usage

```python
# TODO: Add usage example
```

## Components

{self._generate_components_list_markdown()}

## License

This project is licensed under the {self.spec.repo_license} License - see the LICENSE file for details.
'''
        
        with open(readme_path, 'w') as f:
            f.write(content)
        
        logger.info("Generated README.md")
    
    def _generate_license(self) -> None:
        """Generate LICENSE file"""
        license_path = os.path.join(self.output_dir, "LICENSE")
        
        # Simple MIT license for now
        content = f'''MIT License

Copyright (c) {datetime.datetime.now().year} Darby Bailey

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''
        
        with open(license_path, 'w') as f:
            f.write(content)
        
        logger.info("Generated LICENSE")
    
    def _generate_gitignore(self) -> None:
        """Generate .gitignore file"""
        gitignore_path = os.path.join(self.output_dir, ".gitignore")
        
        content = '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/

# Node.js
node_modules/
npm-debug.log
yarn-debug.log
yarn-error.log
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# IDEs
.idea/
.vscode/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
'''
        
        with open(gitignore_path, 'w') as f:
            f.write(content)
        
        logger.info("Generated .gitignore")
    
    def _generate_special_files(self) -> None:
        """Generate any special files specified in the spec"""
        # This is a placeholder for now
        pass
    
    def _generate_components_list_markdown(self) -> str:
        """Generate markdown list of components"""
        if not self.spec.components:
            return "No components defined."
        
        component_list = []
        for component in self.spec.components:
            name = component.get('name', 'unknown')
            description = component.get('description', '')
            component_list.append(f"- **{name}**: {description}")
        
        return "\n".join(component_list)
    
    def _generate_features_list_markdown(self) -> str:
        """Generate markdown list of features"""
        if not self.spec.features:
            return "No features defined."
        
        feature_list = []
        for feature in self.spec.features:
            name = feature.get('name', 'unknown')
            description = feature.get('description', '')
            feature_list.append(f"- **{name}**: {description}")
        
        return "\n".join(feature_list)


class GitHubClient:
    """Client for interacting with GitHub API"""
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize the GitHub API client
        
        Args:
            token: GitHub personal access token
        """
        self.token = token or os.environ.get('GITHUB_TOKEN')
        self.api_url = "https://api.github.com"
        
        if not self.token:
            logger.warning("No GitHub token provided. Repository creation will be skipped.")
    
    def create_repository(self, spec: RepositorySpec) -> Optional[str]:
        """
        Create a repository on GitHub
        
        Args:
            spec: Repository specification
            
        Returns:
            Repository URL if creation was successful, None otherwise
        """
        if not self.token:
            logger.warning("Skipping repository creation: No GitHub token provided")
            return None
        
        logger.info(f"Creating repository: {spec.repo_name}")
        
        headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        data = {
            'name': spec.repo_name,
            'description': spec.repo_description,
            'private': spec.repo_visibility != 'public',
            'auto_init': False,
            'has_issues': True,
            'has_projects': True,
            'has_wiki': True
        }
        
        try:
            response = requests.post(f"{self.api_url}/user/repos", headers=headers, json=data)
            response.raise_for_status()
            repo_url = response.json()['clone_url']
            logger.info(f"Repository created: {repo_url}")
            
            # Add topics if specified
            if spec.repo_topics:
                self._add_topics(spec.repo_name, spec.repo_topics)
            
            return repo_url
        except requests.RequestException as e:
            logger.error(f"Failed to create repository: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            return None
    
    def _add_topics(self, repo_name: str, topics: List[str]) -> None:
        """
        Add topics to a repository
        
        Args:
            repo_name: Repository name
            topics: List of topics to add
        """
        if not self.token:
            return
        
        headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.mercy-preview+json'  # Required for topics API
        }
        
        data = {
            'names': topics
        }
        
        try:
            username = self._get_authenticated_username()
            if not username:
                logger.warning("Could not determine authenticated username. Skipping topics addition.")
                return
            
            response = requests.put(
                f"{self.api_url}/repos/{username}/{repo_name}/topics",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            logger.info(f"Added topics to repository: {topics}")
        except requests.RequestException as e:
            logger.error(f"Failed to add topics to repository: {e}")
    
    def _get_authenticated_username(self) -> Optional[str]:
        """
        Get the authenticated user's username
        
        Returns:
            Username if successful, None otherwise
        """
        if not self.token:
            return None
        
        headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        try:
            response = requests.get(f"{self.api_url}/user", headers=headers)
            response.raise_for_status()
            return response.json()['login']
        except requests.RequestException as e:
            logger.error(f"Failed to get authenticated user: {e}")
            return None


class RepositoryManager:
    """Manages the repository creation and file generation process"""
    
    def __init__(
        self, 
        spec_path: str, 
        output_dir: Optional[str] = None,
        github_token: Optional[str] = None
    ):
        """
        Initialize the repository manager
        
        Args:
            spec_path: Path to the specification file
            output_dir: Directory to output the repository files
            github_token: GitHub personal access token
        """
        self.spec_path = spec_path
        self.spec = RepositorySpec(spec_path)
        
        # Use repository name as output directory if not specified
        self.output_dir = output_dir or os.path.join(os.getcwd(), self.spec.repo_name)
        
        self.github_client = GitHubClient(github_token)
        self.file_generator = FileGenerator(self.spec, self.output_dir)
    
    def build(self) -> None:
        """
        Build the repository
        """
        logger.info("Starting Foundry Complete Repository Builder v0.3")
        logger.info(f"Project name: {self.spec.repo_name}")
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Generate files
        self.file_generator.generate_all()
        
        # Initialize git repository
        self._init_git_repository()
        
        # Create GitHub repository
        repo_url = self.github_client.create_repository(self.spec)
        
        if repo_url:
            # Add remote and push
            self._push_to_remote(repo_url)
            logger.info(f"Repository successfully created and pushed to {repo_url}")
        else:
            logger.info(f"Repository files generated at {self.output_dir}")
    
    def _init_git_repository(self) -> None:
        """Initialize a git repository in the output directory"""
        try:
            subprocess.run(['git', 'init'], cwd=self.output_dir, check=True, capture_output=True)
            subprocess.run(['git', 'add', '.'], cwd=self.output_dir, check=True, capture_output=True)
            subprocess.run(
                ['git', 'commit', '-m', f"Initial commit for {self.spec.repo_name}"],
                cwd=self.output_dir,
                check=True,
                capture_output=True
            )
            logger.info("Git repository initialized")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to initialize git repository: {e}")
            logger.error(f"Stdout: {e.stdout.decode() if e.stdout else ''}")
            logger.error(f"Stderr: {e.stderr.decode() if e.stderr else ''}")
    
    def _push_to_remote(self, repo_url: str) -> None:
        """
        Push the repository to the remote
        
        Args:
            repo_url: URL of the remote repository
        """
        try:
            subprocess.run(
                ['git', 'remote', 'add', 'origin', repo_url],
                cwd=self.output_dir,
                check=True,
                capture_output=True
            )
            subprocess.run(
                ['git', 'push', '-u', 'origin', 'master'],
                cwd=self.output_dir,
                check=True,
                capture_output=True
            )
            logger.info(f"Repository pushed to remote: {repo_url}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to push to remote: {e}")
            logger.error(f"Stdout: {e.stdout.decode() if e.stdout else ''}")
            logger.error(f"Stderr: {e.stderr.decode() if e.stderr else ''}")


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Darby Foundry - Repository Builder")
    parser.add_argument(
        "--spec",
        required=True,
        help="Path to the specification YAML file"
    )
    parser.add_argument(
        "--token",
        help="GitHub personal access token (or set GITHUB_TOKEN environment variable)"
    )
    parser.add_argument(
        "--output-dir",
        help="Directory to output the repository files (defaults to repository name)"
    )
    return parser.parse_args()


def main():
    """Main entry point"""
    args = parse_arguments()
    
    try:
        manager = RepositoryManager(
            spec_path=args.spec,
            output_dir=args.output_dir,
            github_token=args.token
        )
        manager.build()
    except FoundryError as e:
        logger.error(f"Foundry error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
    
    def _generate_components_list_markdown(self) -> str:
    """Generate markdown list of components"""
    if not self.spec.components:
        logger.info("No components defined in spec")
        return "No components defined."
    
    component_list = []
    for component in self.spec.components:
        if not isinstance(component, dict):
            logger.warning(f"Skipping invalid component: {component}")
            continue
        name = component.get('name', 'unknown')
        description = component.get('description', '')
        try:
            component_list.append(f"- **{name}**: {description}")
        except Exception as e:
            logger.error(f"Failed to format component {name}: {e}")
            component_list.append(f"- **{name}**: Error in description")
    
    return "\n".join(component_list) if component_list else "No valid components defined."

def _generate_features_list_markdown(self) -> str:
    """Generate markdown list of features"""
    if not self.spec.features:
        logger.info("No features defined in spec")
        return "No features defined."
    
    feature_list = []
    for feature in self.spec.features:
        if not isinstance(feature, dict):
            logger.warning(f"Skipping invalid feature: {feature}")
            continue
        name = feature.get('name', 'unknown')
        description = feature.get('description', '')
        try:
            feature_list.append(f"- **{name}**: {description}")
        except Exception as e:
            logger.error(f"Failed to format feature {name}: {e}")
            feature_list.append(f"- **{name}**: Error in description")
    
    return "\n".join(feature_list) if feature_list else "No valid features defined."