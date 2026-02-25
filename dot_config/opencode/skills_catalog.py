"""Catalog resolution, validation, and skill file loading."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml


class SkillsLoaderError(Exception):
    """Base exception for skills loader errors."""

    pass


class SkillsCatalog:
    """Handles catalog loading, validation, and skill lookups."""

    _META_KEYS = {"path", "keywords", "tokens", "priority", "order"}

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.catalog = self._load_catalog()
        self.core = self._load_core()

    # --- YAML Loading ---

    def _load_yaml_file(self, path: Path) -> Optional[Dict]:
        """Safely load a YAML file."""
        if not path.exists():
            return None
        try:
            return yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception as e:
            raise SkillsLoaderError(f"Failed to load {path}: {e}")

    def _load_catalog(self) -> Dict:
        catalog_path = self.base_path / "skills_catalog.yaml"
        catalog = self._load_yaml_file(catalog_path)
        if catalog is None:
            raise SkillsLoaderError(f"Catalog file not found: {catalog_path}")
        return catalog

    def _load_core(self) -> Dict:
        core_path = self.base_path / "skills_core.yaml"
        core = self._load_yaml_file(core_path)
        if core is None:
            raise SkillsLoaderError(f"Core skills file not found: {core_path}")
        return core

    def load_skill_content(self, skill_path: Path) -> Optional[Dict]:
        """Load a single skill YAML file."""
        if not skill_path.exists():
            return None
        try:
            return yaml.safe_load(skill_path.read_text(encoding="utf-8"))
        except Exception:
            return None

    # --- Key Access ---

    @staticmethod
    def get_value(meta: Dict, key: str, default: Any = None) -> Any:
        """Get value from metadata by canonical key name."""
        return meta.get(key, default)

    def parse_keywords(self, meta: Dict) -> List[str]:
        """Parse keywords from catalog metadata (list or pipe-separated string)."""
        kw_value = meta.get("keywords", [])
        if isinstance(kw_value, list):
            return kw_value
        elif isinstance(kw_value, str):
            return [k.strip() for k in kw_value.split("|") if k.strip()]
        else:
            return []

    # --- Catalog Structure Detection ---

    def catalog_is_flat(self, catalog_data: Dict) -> bool:
        """Detect flat catalog (skill -> meta) vs categorized (category -> skills)."""
        if not isinstance(catalog_data, dict):
            return False
        for value in catalog_data.values():
            if isinstance(value, dict) and any(k in value for k in self._META_KEYS):
                return True
        return False

    def get_catalog_data(self) -> Dict:
        """Get the catalog data section."""
        return self.catalog.get("catalog", {})

    def get_load_config(self) -> Dict:
        """Get the load strategy configuration."""
        return self.catalog.get("load", {})

    def get_max_tokens(self) -> int:
        """Get the token budget ceiling."""
        load_cfg = self.get_load_config()
        return int(load_cfg.get("max_tokens", 5000))

    # --- Skill Lookups ---

    def find_skill(self, catalog_data: Dict, skill_name: str) -> Optional[Dict]:
        """Find skill metadata by name in catalog data."""
        if self.catalog_is_flat(catalog_data):
            return catalog_data.get(skill_name)
        else:
            for _category, skills in catalog_data.items():
                if isinstance(skills, dict) and skill_name in skills:
                    return skills[skill_name]
        return None

    def iterate_skills(self, catalog_data: Dict):
        """Iterate over (skill_name, meta) pairs from catalog data."""
        if self.catalog_is_flat(catalog_data):
            yield from catalog_data.items()
        else:
            for _category, skills in catalog_data.items():
                if isinstance(skills, dict):
                    yield from skills.items()

    # --- Validation ---

    @staticmethod
    def _is_int_like(value) -> bool:
        if isinstance(value, bool):
            return False
        if isinstance(value, int):
            return True
        if isinstance(value, str):
            return value.isdigit()
        return False

    def validate(self, warn_duplicate_keywords: bool = False) -> List[str]:
        """Validate the catalog structure and references."""
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
                if kw not in all_keywords:
                    all_keywords[kw] = []
                all_keywords[kw].append(skill_name)

        # Validate always-load references
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

    # --- Preset Resolution ---

    def resolve_preset(self, preset: str) -> List[Tuple[str, Dict]]:
        """Resolve a preset name to a list of (skill_name, meta) tuples."""
        presets = self.catalog.get("presets", {})
        if preset not in presets:
            available = sorted(presets.keys()) if presets else []
            raise SkillsLoaderError(
                f"Preset '{preset}' not found. Available: {available}"
            )

        skill_names = presets[preset]
        catalog_data = self.get_catalog_data()

        result: List[Tuple[str, Dict]] = []
        for name in skill_names:
            meta = self.find_skill(catalog_data, name)
            if meta is None:
                raise SkillsLoaderError(
                    f"Preset '{preset}' references unknown skill '{name}'"
                )
            result.append((name, meta))

        return result
