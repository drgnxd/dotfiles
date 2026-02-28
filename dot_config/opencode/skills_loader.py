#!/usr/bin/env python3
"""Skills loader with thinking framework support.

Loads core skills, always-load skills, and task-specific skills
within a token budget.  Supports presets and ordered loading.

Usage: run as script or import SkillsLoader

Architecture:
    IO / YAML loading   -> _CatalogIO
    Keyword matching     -> _Matcher
    Token estimation     -> _Formatter
    Orchestration        -> SkillsLoader  (public API)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml


# ====================================================================
# Exceptions
# ====================================================================


class SkillsLoaderError(Exception):
    """Base exception for skills loader errors."""


# ====================================================================
# Constants
# ====================================================================


class ThinkingMode:
    """Thinking mode constants."""

    SIMPLE: str = "simple"
    MEDIUM: str = "medium"
    COMPLEX: str = "complex"


# ====================================================================
# IO layer – pure file / YAML operations
# ====================================================================


class _CatalogIO:
    """Load and parse catalog / skill YAML files.

    All disk IO is isolated here so the rest of the code stays pure.
    """

    _META_KEYS: frozenset[str] = frozenset(
        {"path", "keywords", "tokens", "priority", "order"}
    )

    def __init__(self, base_path: Path) -> None:
        self.base_path = base_path
        self.catalog: Dict[str, Any] = self._load_required("skills_catalog.yaml")
        self.core: Dict[str, Any] = self._load_required("skills_core.yaml")

    # -- low-level helpers --------------------------------------------------

    def _load_yaml(self, path: Path) -> Optional[Dict[str, Any]]:
        if not path.exists():
            return None
        try:
            return yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception as e:
            raise SkillsLoaderError(f"Failed to load {path}: {e}") from e

    def _load_required(self, filename: str) -> Dict[str, Any]:
        path = self.base_path / filename
        data = self._load_yaml(path)
        if data is None:
            raise SkillsLoaderError(f"Required file not found: {path}")
        return data

    def load_skill_content(self, skill_path: Path) -> Optional[Dict[str, Any]]:
        """Load a single skill YAML file.  Returns None on missing / error."""
        if not skill_path.exists():
            return None
        try:
            return yaml.safe_load(skill_path.read_text(encoding="utf-8"))
        except Exception:
            return None

    # -- catalog structure helpers ------------------------------------------

    @staticmethod
    def get_value(meta: Dict[str, Any], key: str, default: Any = None) -> Any:
        return meta.get(key, default)

    def parse_keywords(self, meta: Dict[str, Any]) -> List[str]:
        """Parse keywords (list or pipe-separated string)."""
        kw_value = meta.get("keywords", [])
        if isinstance(kw_value, list):
            return kw_value
        if isinstance(kw_value, str):
            return [k.strip() for k in kw_value.split("|") if k.strip()]
        return []

    def catalog_is_flat(self, catalog_data: Dict[str, Any]) -> bool:
        """Detect flat (skill -> meta) vs categorized (category -> skills)."""
        if not isinstance(catalog_data, dict):
            return False
        for value in catalog_data.values():
            if isinstance(value, dict) and any(k in value for k in self._META_KEYS):
                return True
        return False

    def get_catalog_data(self) -> Dict[str, Any]:
        return self.catalog.get("catalog", {})

    def get_load_config(self) -> Dict[str, Any]:
        return self.catalog.get("load", {})

    def get_max_tokens(self) -> int:
        return int(self.get_load_config().get("max_tokens", 5000))

    # -- skill iteration / lookup -------------------------------------------

    def find_skill(
        self, catalog_data: Dict[str, Any], skill_name: str
    ) -> Optional[Dict[str, Any]]:
        if self.catalog_is_flat(catalog_data):
            return catalog_data.get(skill_name)
        for _cat, skills in catalog_data.items():
            if isinstance(skills, dict) and skill_name in skills:
                return skills[skill_name]
        return None

    def iterate_skills(
        self, catalog_data: Dict[str, Any]
    ) -> List[Tuple[str, Dict[str, Any]]]:
        """Return (name, meta) pairs from catalog data."""
        pairs: List[Tuple[str, Dict[str, Any]]] = []
        if self.catalog_is_flat(catalog_data):
            pairs = list(catalog_data.items())
        else:
            for _cat, skills in catalog_data.items():
                if isinstance(skills, dict):
                    pairs.extend(skills.items())
        return pairs

    # -- validation ---------------------------------------------------------

    @staticmethod
    def _is_int_like(value: Any) -> bool:
        if isinstance(value, bool):
            return False
        if isinstance(value, int):
            return True
        if isinstance(value, str):
            return value.isdigit()
        return False

    def validate(self, warn_duplicate_keywords: bool = False) -> List[str]:
        """Validate catalog structure and references."""
        errors: List[str] = []
        catalog = self.catalog

        if not isinstance(catalog, dict):
            return ["skills_catalog.yaml must be a mapping"]

        load_cfg = self.get_load_config()
        if not isinstance(load_cfg, dict):
            errors.append("load must be a mapping")
        else:
            always = load_cfg.get("always")
            if always is None:
                errors.append("load.always is required")
            elif not isinstance(always, list) or not all(
                isinstance(item, str) for item in always
            ):
                errors.append("load.always must be a list of strings")

            max_tokens = load_cfg.get("max_tokens")
            if max_tokens is None:
                errors.append("load.max_tokens is required")
            elif not self._is_int_like(max_tokens):
                errors.append("load.max_tokens must be an integer")

        catalog_data = self.get_catalog_data()
        if not isinstance(catalog_data, dict):
            errors.append("catalog must be a mapping")
            return errors

        skill_names: List[str] = []
        all_keywords: Dict[str, List[str]] = {}

        for skill_name, meta in self.iterate_skills(catalog_data):
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

            token_value = meta.get("tokens")
            if token_value is not None and not self._is_int_like(token_value):
                errors.append(f"Skill '{skill_name}' tokens must be an integer")

            kw_value = meta.get("keywords")
            if kw_value is not None and not isinstance(kw_value, (list, str)):
                errors.append(f"Skill '{skill_name}' keywords must be a list or string")

            keywords = self.parse_keywords(meta)
            for kw in keywords:
                if kw.startswith(".") or kw.startswith("\\."):
                    continue
                all_keywords.setdefault(kw, []).append(skill_name)

        # always-load references
        if isinstance(load_cfg, dict):
            always = load_cfg.get("always", [])
            if isinstance(always, list):
                known = set(skill_names)
                for name in always:
                    if name == "skills_core.yaml":
                        continue
                    if name not in known:
                        errors.append(
                            f"Always-load skill '{name}' not found in catalog. "
                            f"Available: {sorted(known)}"
                        )

        if warn_duplicate_keywords:
            for kw, owners in all_keywords.items():
                if len(owners) > 1:
                    errors.append(
                        f"Keyword '{kw}' is shared by multiple skills: {owners} "
                        f"(may cause unintended loading)"
                    )

        # presets
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
                    unknown = [n for n in preset_skills if n not in known]
                    if unknown:
                        errors.append(
                            f"Preset '{preset_name}' references unknown skills: "
                            f"{unknown}"
                        )

        # think_mode
        mode_cfg = catalog.get("think_mode")
        if not isinstance(mode_cfg, dict):
            errors.append("think_mode must be a mapping")
        else:
            for mode in ("simple", "medium", "complex"):
                mode_entry = mode_cfg.get(mode)
                if not isinstance(mode_entry, dict):
                    errors.append(f"Thinking mode '{mode}' must be a mapping")
                    continue
                patterns = mode_entry.get("patterns")
                if not isinstance(patterns, list) or not all(
                    isinstance(item, str) for item in patterns
                ):
                    errors.append(
                        f"Thinking mode '{mode}' patterns must be a list of strings"
                    )

        return errors

    # -- preset resolution --------------------------------------------------

    def resolve_preset(self, preset: str) -> List[Tuple[str, Dict[str, Any]]]:
        presets = self.catalog.get("presets", {})
        if preset not in presets:
            available = sorted(presets.keys()) if presets else []
            raise SkillsLoaderError(
                f"Preset '{preset}' not found. Available: {available}"
            )
        catalog_data = self.get_catalog_data()
        result: List[Tuple[str, Dict[str, Any]]] = []
        for name in presets[preset]:
            meta = self.find_skill(catalog_data, name)
            if meta is None:
                raise SkillsLoaderError(
                    f"Preset '{preset}' references unknown skill '{name}'"
                )
            result.append((name, meta))
        return result


# ====================================================================
# Matcher – keyword matching & thinking mode detection
# ====================================================================


class _Matcher:
    """Keyword matching and thinking mode detection (stateless)."""

    def __init__(self, io: _CatalogIO) -> None:
        self._io = io

    # -- keyword matching ---------------------------------------------------

    @staticmethod
    def matches_keywords(task: str, keywords: List[str]) -> bool:
        """Word-boundary-aware keyword matching.

        Three strategies:
          - File extensions (.py, \\.py): substring match
          - Regex patterns: regex match
          - Plain words: word boundary match
        """
        for kw in keywords:
            if kw.startswith(".") or kw.startswith("\\."):
                clean_ext = kw.lstrip("\\")
                if clean_ext in task:
                    return True
            else:
                pattern = r"(?:^|[^a-z0-9_])" + re.escape(kw) + r"(?:[^a-z0-9_]|$)"
                if re.search(pattern, task):
                    return True
        return False

    # -- thinking mode detection --------------------------------------------

    def detect_thinking_mode(self, task: str) -> str:
        """Detect thinking mode (complex > simple > medium > default medium)."""
        task_lower = task.lower()
        mode_config = self._io.catalog.get("think_mode", {})

        for mode_name in ("complex", "simple", "medium"):
            cfg = mode_config.get(mode_name, {})
            for p in cfg.get("patterns", []):
                if re.search(p, task_lower):
                    return mode_name

        return ThinkingMode.MEDIUM

    # -- task analysis ------------------------------------------------------

    def analyze_task_keywords(self, task: str) -> List[Tuple[str, Dict[str, Any]]]:
        """Return matching skills sorted by (priority, order)."""
        task_lower = task.lower()
        catalog_data = self._io.get_catalog_data()
        matched: List[Tuple[str, Dict[str, Any]]] = []

        for skill_name, meta in self._io.iterate_skills(catalog_data):
            if not isinstance(meta, dict):
                continue
            keywords = self._io.parse_keywords(meta)
            if self.matches_keywords(task_lower, keywords):
                matched.append((skill_name, meta))

        def _sort_key(x: Tuple[str, Dict[str, Any]]) -> Tuple[int, int]:
            pri = 0 if x[1].get("priority") == "high" else 1
            try:
                order = int(x[1].get("order", 99))
            except (TypeError, ValueError):
                order = 99
            return (pri, order)

        matched.sort(key=_sort_key)
        return matched

    # -- always-load resolution ---------------------------------------------

    def resolve_always_load(
        self, task_skills: List[Tuple[str, Dict[str, Any]]]
    ) -> List[Tuple[str, Dict[str, Any]]]:
        """Prepend always-load skills that aren't already present."""
        always_names: List[str] = self._io.get_load_config().get("always", [])
        loaded_names = {name for name, _ in task_skills}
        catalog_data = self._io.get_catalog_data()

        prepend: List[Tuple[str, Dict[str, Any]]] = []
        for name in always_names:
            if name == "skills_core.yaml" or name in loaded_names:
                continue
            meta = self._io.find_skill(catalog_data, name)
            if meta is not None:
                prepend.append((name, meta))
                loaded_names.add(name)

        return prepend + list(task_skills)


# ====================================================================
# Formatter – token estimation & output rendering
# ====================================================================


class _Formatter:
    """Token estimation and output rendering."""

    def __init__(self, catalog: Dict[str, Any]) -> None:
        self._catalog = catalog

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Heuristic token estimation.

        4 chars/token for English-dominant, 3 chars/token when >30% Japanese.
        """
        if not text:
            return 0
        total = len(text)
        jp_chars = sum(1 for c in text if ord(c) > 0x3000)
        divisor = 3 if jp_chars > total * 0.3 else 4
        return max(1, total // divisor)

    def format_thinking_header(self, mode: str) -> str:
        mode_cfg = self._catalog.get("think_mode", {}).get(mode, {})
        overhead = mode_cfg.get("budget", "?")
        return (
            f"\n# Thinking Mode: {mode.upper()}\n# Overhead budget: {overhead} tokens\n"
        )

    def format_output(
        self,
        core_content: str,
        thinking_mode: str,
        skills: List[Tuple[str, str, Optional[Dict[str, Any]]]],
        tokens_used: int,
        max_tokens: int,
    ) -> str:
        parts: List[str] = [
            "# Core Skills (Always Loaded)\n",
            core_content,
            self.format_thinking_header(thinking_mode),
        ]

        for skill_name, status, skill_content in skills:
            label = skill_name.title()
            if status == "loaded" and skill_content is not None:
                parts.append(f"\n# {label}\n")
                parts.append(yaml.dump(skill_content, default_flow_style=False))
            elif status == "skipped":
                parts.append(f"\n# {label} (skipped - token limit)\n")
            elif status == "missing":
                parts.append(f"\n# {label} (missing file)\n")
            elif status == "error":
                parts.append(f"\n# {label} (error loading)\n")

        parts.append(f"\n# Tokens used: {tokens_used}/{max_tokens}\n")
        parts.append(f"# Thinking mode: {thinking_mode}\n")
        return "".join(parts)


# ====================================================================
# SkillsLoader – public orchestrator
# ====================================================================


class SkillsLoader:
    """Load and manage AI agent skills with thinking framework support.

    Public API consumed by tests and external callers.
    Delegates IO, matching, and formatting to private helper classes.
    """

    CORE_TOKENS_ESTIMATE: int = 200

    def __init__(self, base_path: Path = Path(__file__).resolve().parent) -> None:
        self.base_path = base_path
        self._io = _CatalogIO(base_path)
        self._matcher = _Matcher(self._io)
        self._formatter = _Formatter(self._io.catalog)

        # Expose for backward compatibility with tests
        self.catalog: Dict[str, Any] = self._io.catalog
        self.core: Dict[str, Any] = self._io.core

    # -- Delegated methods (backward-compatible public API) -----------------

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        return _Formatter.estimate_tokens(text)

    def _load_skill_content(self, skill_path: Path) -> Optional[Dict[str, Any]]:
        return self._io.load_skill_content(skill_path)

    def _get_catalog_value(
        self, meta: Dict[str, Any], key: str, default: Any = None
    ) -> Any:
        return _CatalogIO.get_value(meta, key, default)

    def _parse_keywords(self, meta: Dict[str, Any]) -> List[str]:
        return self._io.parse_keywords(meta)

    def _matches_keywords(self, task: str, keywords: List[str]) -> bool:
        return _Matcher.matches_keywords(task, keywords)

    def _catalog_is_flat(self, catalog_data: Dict[str, Any]) -> bool:
        return self._io.catalog_is_flat(catalog_data)

    def _detect_thinking_mode(self, task: str) -> str:
        return self._matcher.detect_thinking_mode(task)

    def _analyze_task_keywords(self, task: str) -> List[Tuple[str, Dict[str, Any]]]:
        return self._matcher.analyze_task_keywords(task)

    def _resolve_always_load(
        self, task_skills: List[Tuple[str, Dict[str, Any]]]
    ) -> List[Tuple[str, Dict[str, Any]]]:
        return self._matcher.resolve_always_load(task_skills)

    def _find_skill_in_catalog(
        self, catalog_data: Dict[str, Any], skill_name: str
    ) -> Optional[Dict[str, Any]]:
        return self._io.find_skill(catalog_data, skill_name)

    def validate_catalog(self, warn_duplicate_keywords: bool = False) -> List[str]:
        return self._io.validate(warn_duplicate_keywords)

    def _resolve_preset(self, preset: str) -> List[Tuple[str, Dict[str, Any]]]:
        return self._io.resolve_preset(preset)

    # -- Main entry ---------------------------------------------------------

    def load_for_task(self, task: str, preset: Optional[str] = None) -> str:
        """Load relevant skills for a given task.

        Flow:
            1. Detect thinking mode from task description
            2. Find keyword-matched skills (or use preset)
            3. Prepend always-load skills
            4. Load each skill within token budget
            5. Format and return output
        """
        thinking_mode = self._detect_thinking_mode(task)
        max_tokens = self._io.get_max_tokens()

        if preset is not None:
            task_skills = self._resolve_preset(preset)
        else:
            task_skills = self._analyze_task_keywords(task)

        all_skills = self._resolve_always_load(task_skills)

        # Core content tokens
        core_content = yaml.dump(self.core, default_flow_style=False)
        tokens_used = self._estimate_tokens(core_content)

        # Load each skill within budget
        loaded: List[Tuple[str, str, Optional[Dict[str, Any]]]] = []
        for skill_name, meta in all_skills:
            skill_path = self.base_path / "skills" / meta.get("path", "")
            skill_content = self._load_skill_content(skill_path)

            if skill_content is None:
                status = "missing" if not skill_path.exists() else "error"
                loaded.append((skill_name, status, None))
                continue

            skill_text = yaml.dump(skill_content, default_flow_style=False)
            measured = self._estimate_tokens(skill_text)
            try:
                catalog_tokens = int(self._get_catalog_value(meta, "tokens", 0))
            except (TypeError, ValueError):
                catalog_tokens = 0
            skill_tokens = max(measured, catalog_tokens)

            if tokens_used + skill_tokens > max_tokens:
                loaded.append((skill_name, "skipped", None))
                continue

            loaded.append((skill_name, "loaded", skill_content))
            tokens_used += skill_tokens

        return self._formatter.format_output(
            core_content, thinking_mode, loaded, tokens_used, max_tokens
        )


# ====================================================================
# CLI
# ====================================================================


def _run_validation(strict: bool = False) -> int:
    loader = SkillsLoader()
    errors = loader.validate_catalog(warn_duplicate_keywords=strict)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    label = "strict " if strict else ""
    print(f"skills_catalog.yaml {label}validation passed")
    return 0


def main() -> int:
    if "--validate" in sys.argv[1:]:
        return _run_validation()

    if "--validate-strict" in sys.argv[1:]:
        return _run_validation(strict=True)

    # --preset=<name>
    preset: Optional[str] = None
    for arg in sys.argv[1:]:
        if arg.startswith("--preset="):
            preset = arg.split("=", 1)[1]

    loader = SkillsLoader()

    if preset:
        print(f"Loading preset: {preset}")
        try:
            result = loader.load_for_task("preset task", preset=preset)
            print(result)
        except SkillsLoaderError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 1
        return 0

    # Demo mode
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
