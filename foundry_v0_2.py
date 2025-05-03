
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
from typing import Dict, List, Any, Optional
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
        if not isinstance(self.spec_data, dict):
            raise FoundryError("Specification must be a dictionary/mapping")

        if 'repository' not in self.spec_data:
            raise FoundryError("Missing required 'repository' section in specification")

        repo_section = self.spec_data['repository']
        if not isinstance(repo_section, dict):
            raise FoundryError("Repository section must be a dictionary/mapping")

        if 'name' not in repo_section:
            raise FoundryError("Missing required 'name' field in repository section")

        logger.info("Specification validated successfully")

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

        for component in self.spec.components:
            self._generate_component_files(component)

        self._generate_readme()
        self._generate_license()
        self._generate_gitignore()
        self._generate_special_files()

        logger.info("All files generated successfully")

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

            if os.path.exists(full_path):
                logger.info(f"File already exists: {file_path}")
                continue

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

        basename = os.path.basename(file_path)
        filename_without_ext = os.path.splitext(basename)[0]
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")

        if ext == '.py':
            return self._generate_python_file(file_path, name, description)
        elif ext == '.md':
            return self._generate_markdown_file(file_path, name, description)
        elif ext in ['.tsx', '.ts', '.js']:
            return self._generate_typescript_file(file_path, name, description)
        elif ext == '.json':
            return self._generate_json_file(file_path)
        elif ext in ['.yml', '.yaml']:
            return self._generate_yaml_file(file_path)
        else:
            return f"# {os.path.basename(file_path)}\n# Generated by Darby Foundry on {current_date}\n# Component: {name}\n# Description: {description}\n\n# TODO: Implement {filename_without_ext} functionality\n"

    def _generate_python_file(self, file_path: str, component_name: str, description: str) -> str:
        """Generate content for a Python file"""
        basename = os.path.basename(file_path)
        filename_without_ext = os.path.splitext(basename)[0]

        if basename == '__init__.py':
            parent_dir = os.path.basename(os.path.dirname(file_path))
            return f'''"""
{parent_dir} module for {self.spec.repo_name}
"""

__version__ = "0.1.0"
'''

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

if __name__ == "__main__":
    instance = {class_name}()
    instance.run()
'''

def _generate_markdown_file(self, file_path: str, component_name: str, description: str) -> str:
    """Generate content for a Markdown file"""
    basename = os.path.basename(file_path)
    filename_without_ext = os.path.splitext(basename)[0]
    title = ' '.join(word.capitalize() for word in filename_without_ext.split('_'))

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
    else:
        return f'''# {title}

{description}

## Overview

TODO: Add overview for {title}

## Usage

TODO: Add usage instructions

## Reference

TODO: Add reference documentation
'''