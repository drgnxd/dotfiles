#!/usr/bin/env python3
"""Skills loader with thinking framework support - Optimized.

Supports both original and optimized catalog key names.
Loads core skills, always-load skills (japanese, thinking),
and task-specific skills within a token budget.

Usage: run as script or import SkillsLoader
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import yaml


class SkillsLoaderError(Exception):
    """Base exception for skills loader errors."""

    pass


class ThinkingMode:
    """Thinking mode constants."""

    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


class SkillsLoader:
    """Load and manage AI agent skills with thinking framework support."""

    CORE_TOKENS_ESTIMATE = 200  # Reduced from 500

    def __init__(self, base_path: Path = Path(__file__).resolve().parent):
        """Initialize the skills loader.

        Args:
            base_path: Directory containing skills YAML files.
        """
        self.base_path = base_path
        self.catalog = self._load_catalog()
        self.core = self._load_core()

    # --- YAML Loading ---

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
            return yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception as e:
            raise SkillsLoaderError(f"Failed to load {path}: {e}")

    def _load_catalog(self) -> Dict:
        """Load the skills catalog.

        Returns:
            Catalog dictionary.

        Raises:
            SkillsLoaderError: If catalog file is missing or invalid.
        """
        catalog_path = self.base_path / "skills_catalog.yaml"
        catalog = self._load_yaml_file(catalog_path)
        if catalog is None:
            raise SkillsLoaderError(f"Catalog file not found: {catalog_path}")
        return catalog

    def _load_core(self) -> Dict:
        """Load core skills.

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

    def _is_int_like(self, value) -> bool:
        if isinstance(value, bool):
            return False
        if isinstance(value, int):
            return True
        if isinstance(value, str):
            return value.isdigit()
        return False

    def validate_catalog(self) -> List[str]:
        errors: List[str] = []
        catalog = self.catalog

        if not isinstance(catalog, dict):
            return ["skills_catalog.yaml must be a mapping"]

        load_cfg = catalog.get("load_strategy") or catalog.get("load")
        if not isinstance(load_cfg, dict):
            errors.append("load or load_strategy must be a mapping")
        else:
            always = load_cfg.get("always")
            if always is None:
                errors.append("load.always is required")
            elif not isinstance(always, list) or not all(
                isinstance(item, str) for item in always
            ):
                errors.append("load.always must be a list of strings")

            max_tokens = load_cfg.get("max_tokens") or load_cfg.get("max_tok")
            if max_tokens is None:
                errors.append("load.max_tokens or load.max_tok is required")
            elif not self._is_int_like(max_tokens):
                errors.append("load.max_tokens must be an integer")

        catalog_data = catalog.get("catalog") or catalog.get("cat")
        if not isinstance(catalog_data, dict):
            errors.append("catalog or cat must be a mapping")
            return errors

        skill_names: List[str] = []
        if self._catalog_is_flat(catalog_data):
            items = catalog_data.items()
        else:
            items = []
            for _category, skills in catalog_data.items():
                if isinstance(skills, dict):
                    items.extend(skills.items())

        for skill_name, meta in items:
            skill_names.append(skill_name)
            if not isinstance(meta, dict):
                errors.append(f"Skill '{skill_name}' metadata must be a mapping")
                continue

            path_value = meta.get("path")
            if not isinstance(path_value, str) or not path_value.strip():
                errors.append(f"Skill '{skill_name}' is missing a valid path")
            else:
                skill_path = self.base_path / "skills" / path_value
                if not skill_path.exists():
                    errors.append(f"Skill '{skill_name}' path not found: {skill_path}")

            token_value = self._get_catalog_value(meta, "tokens")
            if token_value is None:
                errors.append(f"Skill '{skill_name}' is missing tokens")
            elif not self._is_int_like(token_value):
                errors.append(f"Skill '{skill_name}' tokens must be an integer")

            kw_value = self._get_catalog_value(meta, "trigger_keywords")
            if kw_value is not None and not isinstance(kw_value, (list, str)):
                errors.append(f"Skill '{skill_name}' keywords must be a list or string")

        presets = catalog.get("presets")
        if presets is not None:
            if not isinstance(presets, dict):
                errors.append("presets must be a mapping")
            else:
                known = set(skill_names)
                for preset_name, preset_skills in presets.items():
                    if not isinstance(preset_skills, list) or not all(
                        isinstance(item, str) for item in preset_skills
                    ):
                        errors.append(
                            f"Preset '{preset_name}' must be a list of skill names"
                        )
                        continue
                    unknown = [name for name in preset_skills if name not in known]
                    if unknown:
                        errors.append(
                            f"Preset '{preset_name}' references unknown skills: {unknown}"
                        )

        mode_cfg = catalog.get("thinking_mode_auto_detect") or catalog.get("think_mode")
        if not isinstance(mode_cfg, dict):
            errors.append("think_mode or thinking_mode_auto_detect must be a mapping")
        else:
            for mode in (
                ThinkingMode.SIMPLE,
                ThinkingMode.MEDIUM,
                ThinkingMode.COMPLEX,
            ):
                mode_entry = mode_cfg.get(mode)
                if not isinstance(mode_entry, dict):
                    errors.append(f"Thinking mode '{mode}' must be a mapping")
                    continue
                patterns = mode_entry.get("patterns") or mode_entry.get("pat")
                if not isinstance(patterns, list) or not all(
                    isinstance(item, str) for item in patterns
                ):
                    errors.append(
                        f"Thinking mode '{mode}' patterns must be a list of strings"
                    )

        return errors

    def _load_skill_content(self, skill_path: Path) -> Optional[Dict]:
        """Load a single skill file.

        Args:
            skill_path: Path to the skill YAML file.

        Returns:
            Parsed skill content as dict, or None if loading fails.
        """
        if not skill_path.exists():
            return None
        try:
            return yaml.safe_load(skill_path.read_text(encoding="utf-8"))
        except Exception:
            return None

    # --- Catalog Key Normalization ---

    def _get_catalog_value(self, meta: Dict, key: str, default=None):
        """Get value from catalog with key aliasing support.

        Supports both original and optimized key names:
        - trigger_keywords / kw
        - tokens / tok
        - priority / pri

        Args:
            meta: Skill metadata dictionary.
            key: Original key name.
            default: Default value if key not found.

        Returns:
            Value from metadata.
        """
        aliases = {
            "trigger_keywords": ["trigger_keywords", "kw"],
            "tokens": ["tokens", "tok"],
            "priority": ["priority", "pri"],
            "has_tools": ["has_tools", "tools"],
        }

        if key in aliases:
            for alias in aliases[key]:
                if alias in meta:
                    return meta[alias]
        elif key in meta:
            return meta[key]

        return default

    def _parse_keywords(self, meta: Dict) -> List[str]:
        """Parse keywords from catalog metadata.

        Supports both list and pipe-separated string formats.

        Args:
            meta: Skill metadata dictionary.

        Returns:
            List of keyword strings.
        """
        kw_value = self._get_catalog_value(meta, "trigger_keywords", [])

        if isinstance(kw_value, list):
            return kw_value
        elif isinstance(kw_value, str):
            # Pipe-separated format: "py|sh|js"
            return [k.strip() for k in kw_value.split("|") if k.strip()]
        else:
            return []

    def _catalog_is_flat(self, catalog_data: Dict) -> bool:
        """Detect flat catalog mapping (skill -> meta) vs categorized mapping."""
        if not isinstance(catalog_data, dict):
            return False

        meta_keys = {
            "path",
            "kw",
            "trigger_keywords",
            "tok",
            "tokens",
            "pri",
            "priority",
        }

        for value in catalog_data.values():
            if isinstance(value, dict) and any(k in value for k in meta_keys):
                return True

        return False

    # --- Thinking Mode Detection ---

    def _detect_thinking_mode(self, task: str) -> str:
        """Detect appropriate thinking mode based on task description.

        Checks complex patterns first (most specific), then simple,
        then medium. Falls back to medium for ambiguous tasks.

        Args:
            task: Task description to analyze.

        Returns:
            One of ThinkingMode constants.
        """
        task_lower = task.lower()

        # Support both original and optimized catalog structure
        mode_config = self.catalog.get("thinking_mode_auto_detect") or self.catalog.get(
            "think_mode", {}
        )

        # Complex first (highest specificity)
        complex_cfg = mode_config.get("complex", {})
        for pattern in complex_cfg.get("patterns") or complex_cfg.get("pat", []):
            if re.search(pattern, task_lower):
                return ThinkingMode.COMPLEX

        # Simple patterns
        simple_cfg = mode_config.get("simple", {})
        for pattern in simple_cfg.get("patterns") or simple_cfg.get("pat", []):
            if re.search(pattern, task_lower):
                return ThinkingMode.SIMPLE

        # Medium patterns
        medium_cfg = mode_config.get("medium", {})
        for pattern in medium_cfg.get("patterns") or medium_cfg.get("pat", []):
            if re.search(pattern, task_lower):
                return ThinkingMode.MEDIUM

        # Default: medium
        return ThinkingMode.MEDIUM

    # --- Task Analysis ---

    def _analyze_task_keywords(self, task: str) -> List[Tuple[str, Dict]]:
        """Analyze task and return matching skills based on keywords.

        Args:
            task: Task description to analyze.

        Returns:
            List of (skill_name, skill_metadata) sorted by priority.
        """
        task_lower = task.lower()
        skills_to_load: List[Tuple[str, Dict]] = []

        # Support both "catalog" and "cat" keys
        catalog_data = self.catalog.get("catalog") or self.catalog.get("cat", {})

        if self._catalog_is_flat(catalog_data):
            for skill_name, meta in catalog_data.items():
                if not isinstance(meta, dict):
                    continue
                keywords = self._parse_keywords(meta)
                if any(kw in task_lower for kw in keywords):
                    skills_to_load.append((skill_name, meta))
        else:
            for _category, skills in catalog_data.items():
                if not isinstance(skills, dict):
                    continue
                for skill_name, meta in skills.items():
                    if not isinstance(meta, dict):
                        continue
                    keywords = self._parse_keywords(meta)
                    if any(kw in task_lower for kw in keywords):
                        skills_to_load.append((skill_name, meta))

        # Priority sort: high-priority skills first
        def priority_key(x):
            pri = self._get_catalog_value(x[1], "priority")
            return 0 if pri in ("high", "hi") else 1

        skills_to_load.sort(key=priority_key)
        return skills_to_load

    def _resolve_always_load(
        self, task_skills: List[Tuple[str, Dict]]
    ) -> List[Tuple[str, Dict]]:
        """Prepend always-load skills that aren't already in the task list.

        Reads load_strategy.always or load.always from catalog.
        Skips 'skills_core.yaml' (loaded separately via _load_core).

        Args:
            task_skills: Skills already matched by keyword analysis.

        Returns:
            Combined list with always-load skills prepended.
        """
        # Support both "load_strategy" and "load" keys
        load_cfg = self.catalog.get("load_strategy") or self.catalog.get("load", {})
        always_names = load_cfg.get("always", [])
        loaded_names = {name for name, _ in task_skills}

        catalog_data = self.catalog.get("catalog") or self.catalog.get("cat", {})

        prepend: List[Tuple[str, Dict]] = []
        if self._catalog_is_flat(catalog_data):
            for always_name in always_names:
                if always_name == "skills_core.yaml" or always_name in loaded_names:
                    continue
                if always_name in catalog_data:
                    prepend.append((always_name, catalog_data[always_name]))
                    loaded_names.add(always_name)
        else:
            for always_name in always_names:
                if always_name == "skills_core.yaml" or always_name in loaded_names:
                    continue
                # Find in catalog
                for _category, skills in catalog_data.items():
                    if not isinstance(skills, dict):
                        continue
                    if always_name in skills:
                        prepend.append((always_name, skills[always_name]))
                        loaded_names.add(always_name)
                        break

        return prepend + task_skills

    # --- Output Formatting ---

    def _format_thinking_header(self, mode: str) -> str:
        """Format thinking mode header for output.

        Args:
            mode: Detected thinking mode.

        Returns:
            Formatted header string.
        """
        mode_config_root = self.catalog.get(
            "thinking_mode_auto_detect"
        ) or self.catalog.get("think_mode", {})
        mode_config = mode_config_root.get(mode, {})
        overhead = mode_config.get("overhead_budget") or mode_config.get("budget", "?")

        return (
            f"\n# Thinking Mode: {mode.upper()}\n# Overhead budget: {overhead} tokens\n"
        )

    def _format_output(
        self,
        core_content: str,
        thinking_mode: str,
        skills: List[Tuple[str, str, Optional[Dict]]],
        tokens_used: int,
        max_tokens: int,
    ) -> str:
        """Format the final output.

        Args:
            core_content: YAML-formatted core skills.
            thinking_mode: Detected thinking mode.
            skills: List of (skill_name, status, content) tuples.
            tokens_used: Total tokens consumed.
            max_tokens: Token budget ceiling.

        Returns:
            Complete formatted output string.
        """
        output = ["# Core Skills (Always Loaded)\n"]
        output.append(core_content)
        output.append(self._format_thinking_header(thinking_mode))

        for skill_name, status, skill_content in skills:
            if status == "loaded" and skill_content is not None:
                output.append(f"\n# {skill_name.title()}\n")
                output.append(yaml.dump(skill_content, default_flow_style=False))
            elif status == "skipped":
                output.append(f"\n# {skill_name.title()} (skipped - token limit)\n")
            elif status == "missing":
                output.append(f"\n# {skill_name.title()} (missing file)\n")
            elif status == "error":
                output.append(f"\n# {skill_name.title()} (error loading)\n")

        output.append(f"\n# Tokens used: {tokens_used}/{max_tokens}\n")
        output.append(f"# Thinking mode: {thinking_mode}\n")
        return "".join(output)

    # --- Main Entry ---

    def load_for_task(self, task: str) -> str:
        """Load relevant skills for a given task.

        Flow:
            1. Detect thinking mode from task description
            2. Find keyword-matched skills
            3. Prepend always-load skills
            4. Load each skill within token budget
            5. Format and return output

        Args:
            task: Task description to analyze.

        Returns:
            Formatted string with all loaded skills and metadata.
        """
        thinking_mode = self._detect_thinking_mode(task)
        tokens_used = int(self.CORE_TOKENS_ESTIMATE)

        # Support both "load_strategy" and "load" keys
        load_cfg = self.catalog.get("load_strategy") or self.catalog.get("load", {})
        max_tokens = int(load_cfg.get("max_tokens") or load_cfg.get("max_tok", 5000))

        # Resolve full skill list (always-load + keyword-matched)
        all_skills = self._resolve_always_load(self._analyze_task_keywords(task))

        # Core content
        core_content = yaml.dump(self.core, default_flow_style=False)

        # Load each skill within budget
        loaded_skills: List[Tuple[str, str, Optional[Dict]]] = []
        for skill_name, meta in all_skills:
            skill_tokens = self._get_catalog_value(meta, "tokens", 1000)
            skill_tokens = int(skill_tokens) if skill_tokens is not None else 0

            if tokens_used + skill_tokens > max_tokens:
                loaded_skills.append((skill_name, "skipped", None))
                continue

            skill_path = self.base_path / "skills" / meta.get("path", "")
            skill_content = self._load_skill_content(skill_path)

            if skill_content is None:
                status = "missing" if not skill_path.exists() else "error"
                loaded_skills.append((skill_name, status, None))
            else:
                loaded_skills.append((skill_name, "loaded", skill_content))

            tokens_used += skill_tokens

        return self._format_output(
            core_content, thinking_mode, loaded_skills, tokens_used, max_tokens
        )


def _run_validation() -> int:
    loader = SkillsLoader()
    errors = loader.validate_catalog()
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("skills_catalog.yaml validation passed")
    return 0


def main() -> int:
    if "--validate" in sys.argv[1:]:
        return _run_validation()

    loader = SkillsLoader()
    test_tasks = [
        "ls -la",
        "Create a Python script to parse CSV files",
        "Design a fault-tolerant microservices architecture",
    ]

    for task in test_tasks:
        print(f"\n{'=' * 60}")
        print(f"Task: {task}")
        print(f"{'=' * 60}")
        result = loader.load_for_task(task)
        print(result[:800])
        print("[... truncated ...]")
        print(f"Total length: {len(result)} chars (~{len(result) // 4} tokens)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
