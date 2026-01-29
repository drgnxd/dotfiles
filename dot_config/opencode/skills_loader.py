#!/usr/bin/env python3
"""Simple skills loader for token-aware loading.

Usage: run as script or import SkillsLoader
"""
from pathlib import Path
from typing import Dict
import yaml


class SkillsLoader:
    def __init__(self, base_path: Path = Path(__file__).resolve().parent):
        """base_path defaults to the directory containing this script so
        the loader works if the YAMLs and `skills/` are colocated with
        this file.
        """
        self.base_path = base_path
        self.catalog = self._load_catalog()
        self.core = self._load_core()

    def _load_catalog(self) -> Dict:
        catalog_path = self.base_path / "skills_catalog.yaml"
        return yaml.safe_load(catalog_path.read_text())

    def _load_core(self) -> Dict:
        core_path = self.base_path / "skills_core.yaml"
        return yaml.safe_load(core_path.read_text())

    def load_for_task(self, task: str) -> str:
        """タスク記述から必要なスキルをロードして文字列で返す"""
        output = ["# Core Skills (Always Loaded)\n"]
        output.append(yaml.dump(self.core, default_flow_style=False))

        tokens_used = 500
        max_tokens = self.catalog["load_strategy"]["max_tokens"]

        task_lower = task.lower()
        skills_to_load = []

        for category, skills in self.catalog["catalog"].items():
            for skill_name, meta in skills.items():
                keywords = meta.get("trigger_keywords", [])
                if any(kw in task_lower for kw in keywords):
                    skills_to_load.append((skill_name, meta))

        for skill_name, meta in skills_to_load:
            skill_tokens = meta["tokens"]
            if tokens_used + skill_tokens > max_tokens:
                break

            skill_path = self.base_path / "skills" / meta["path"]
            if not skill_path.exists():
                output.append(f"# {skill_name.title()} (missing at {skill_path})\n")
                tokens_used += skill_tokens
                continue

            skill_content = yaml.safe_load(skill_path.read_text())
            output.append(f"\n# {skill_name.title()}\n")
            output.append(yaml.dump(skill_content, default_flow_style=False))
            tokens_used += skill_tokens

        output.append(f"\n# Tokens used: {tokens_used}/{max_tokens}\n")
        return "\n".join(output)


if __name__ == "__main__":
    loader = SkillsLoader()
    task1 = "Create a Python script to parse CSV files"
    print(loader.load_for_task(task1))
