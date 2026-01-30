#!/usr/bin/env python3
"""Simple skills loader for token-aware loading.

Usage: run as script or import SkillsLoader
"""
from pathlib import Path
from typing import Dict, Optional
import yaml


class SkillsLoaderError(Exception):
    """Base exception for skills loader errors."""
    pass


class SkillsLoader:
    """Load and manage AI agent skills based on task descriptions."""
    
    # Base tokens used for core skills (estimated)
    CORE_TOKENS_ESTIMATE = 500
    
    def __init__(self, base_path: Path = Path(__file__).resolve().parent):
        """Initialize the skills loader.
        
        Args:
            base_path: Directory containing skills YAML files. Defaults to the
                      directory containing this script.
        """
        self.base_path = base_path
        self.catalog = self._load_catalog()
        self.core = self._load_core()

    def _load_yaml_file(self, path: Path) -> Optional[Dict]:
        """Safely load a YAML file.
        
        Args:
            path: Path to the YAML file.
            
        Returns:
            Parsed YAML content as dict, or None if file doesn't exist.
            
        Raises:
            SkillsLoaderError: If file exists but cannot be read or parsed.
        """
        if not path.exists():
            return None
            
        try:
            content = path.read_text(encoding='utf-8')
            return yaml.safe_load(content)
        except Exception as e:
            raise SkillsLoaderError(f"Failed to load {path}: {e}")

    def _load_catalog(self) -> Dict:
        """Load the skills catalog from skills_catalog.yaml.
        
        Returns:
            Catalog dictionary with skill metadata.
            
        Raises:
            SkillsLoaderError: If catalog file is missing or invalid.
        """
        catalog_path = self.base_path / "skills_catalog.yaml"
        catalog = self._load_yaml_file(catalog_path)
        
        if catalog is None:
            raise SkillsLoaderError(f"Catalog file not found: {catalog_path}")
            
        return catalog

    def _load_core(self) -> Dict:
        """Load core skills from skills_core.yaml.
        
        Returns:
            Core skills dictionary.
            
        Raises:
            SkillsLoaderError: If core file is missing or invalid.
        """
        core_path = self.base_path / "skills_core.yaml"
        core = self._load_yaml_file(core_path)
        
        if core is None:
            raise SkillsLoaderError(f"Core skills file not found: {core_path}")
            
        return core

    def load_for_task(self, task: str) -> str:
        """Load relevant skills based on task description.
        
        Analyzes the task description to find matching skills based on keywords,
        then loads them while respecting the token budget.
        
        Args:
            task: Task description to analyze.
            
        Returns:
            Formatted string containing loaded skills and token usage info.
        """
        output = ["# Core Skills (Always Loaded)\n"]
        output.append(yaml.dump(self.core, default_flow_style=False))

        tokens_used = self.CORE_TOKENS_ESTIMATE
        max_tokens = self.catalog.get("load_strategy", {}).get("max_tokens", 8000)

        task_lower = task.lower()
        skills_to_load = []

        catalog_data = self.catalog.get("catalog", {})
        for category, skills in catalog_data.items():
            for skill_name, meta in skills.items():
                keywords = meta.get("trigger_keywords", [])
                if any(kw in task_lower for kw in keywords):
                    skills_to_load.append((skill_name, meta))

        for skill_name, meta in skills_to_load:
            skill_tokens = meta.get("tokens", 1000)
            if tokens_used + skill_tokens > max_tokens:
                output.append(f"\n# {skill_name.title()} (skipped - token limit)\n")
                break

            skill_path = self.base_path / "skills" / meta.get("path", "")
            if not skill_path.exists():
                output.append(f"\n# {skill_name.title()} (missing at {skill_path})\n")
                tokens_used += skill_tokens
                continue

            try:
                skill_content = yaml.safe_load(skill_path.read_text())
                output.append(f"\n# {skill_name.title()}\n")
                output.append(yaml.dump(skill_content, default_flow_style=False))
                tokens_used += skill_tokens
            except Exception as e:
                output.append(f"\n# {skill_name.title()} (error loading: {e})\n")

        output.append(f"\n# Tokens used: {tokens_used}/{max_tokens}\n")
        return "".join(output)


if __name__ == "__main__":
    loader = SkillsLoader()
    task1 = "Create a Python script to parse CSV files"
    print(loader.load_for_task(task1))
