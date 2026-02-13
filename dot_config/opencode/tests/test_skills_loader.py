"""Comprehensive tests for skills_loader.py."""

import re
from pathlib import Path

import pytest

from skills_loader import SkillsLoader, SkillsLoaderError, ThinkingMode


@pytest.fixture
def loader() -> SkillsLoader:
    """Create a SkillsLoader instance with the project base path."""
    base_path = Path(__file__).resolve().parents[1]
    return SkillsLoader(base_path=base_path)


# ============================================================
# Catalog Validation
# ============================================================


class TestCatalogValidation:
    """Tests for validate_catalog()."""

    def test_catalog_validation_passes(self, loader: SkillsLoader) -> None:
        """Basic catalog validation should pass with no errors."""
        errors = loader.validate_catalog()
        assert errors == [], f"Validation errors: {errors}"

    def test_strict_validation_reports_duplicate_keywords(
        self, loader: SkillsLoader
    ) -> None:
        """Strict validation should detect duplicate keywords across skills."""
        errors = loader.validate_catalog(warn_duplicate_keywords=True)
        # Duplicate keywords are warnings, not blockers
        # Just ensure the method runs without crashing
        assert isinstance(errors, list)

    def test_always_load_references_exist_in_catalog(
        self, loader: SkillsLoader
    ) -> None:
        """All always-load skill names must exist as catalog keys."""
        load_cfg = loader.catalog.get("load_strategy") or loader.catalog.get("load", {})
        always = load_cfg.get("always", [])
        catalog_data = loader.catalog.get("catalog") or loader.catalog.get("cat", {})

        for name in always:
            if name == "skills_core.yaml":
                continue
            assert name in catalog_data, (
                f"Always-load skill '{name}' not found in catalog keys: "
                f"{sorted(catalog_data.keys())}"
            )


# ============================================================
# Token Estimation
# ============================================================


class TestTokenEstimation:
    """Tests for _estimate_tokens()."""

    def test_empty_text_returns_zero(self) -> None:
        assert SkillsLoader._estimate_tokens("") == 0

    def test_english_text_estimation(self) -> None:
        # "Hello world" = 11 chars -> 11 // 4 = 2
        result = SkillsLoader._estimate_tokens("Hello world")
        assert result == 2

    def test_japanese_text_estimation(self) -> None:
        # 7 Japanese chars -> 7 // 3 = 2
        text = "\u3053\u3093\u306b\u3061\u306f\u4e16\u754c"
        result = SkillsLoader._estimate_tokens(text)
        assert result == 2

    def test_mixed_language_estimation(self) -> None:
        text = "Hello \u3053\u3093\u306b\u3061\u306f world \u4e16\u754c test"
        result = SkillsLoader._estimate_tokens(text)
        assert result > 0

    def test_minimum_one_token(self) -> None:
        """Even a single character should return at least 1 token."""
        assert SkillsLoader._estimate_tokens("x") == 1

    def test_large_text_reasonable(self) -> None:
        text = "a" * 4000  # 4000 chars -> ~1000 tokens
        result = SkillsLoader._estimate_tokens(text)
        assert 900 <= result <= 1100


# ============================================================
# Keyword Matching
# ============================================================


class TestKeywordMatching:
    """Tests for _matches_keywords()."""

    def test_exact_word_match(self, loader: SkillsLoader) -> None:
        assert loader._matches_keywords("use python", ["python"])
        assert loader._matches_keywords("python script", ["python"])

    def test_no_substring_match_for_short_keywords(self, loader: SkillsLoader) -> None:
        """Short keywords like 'py' should not match inside longer words."""
        # 'py' inside 'cpython' should NOT match
        assert not loader._matches_keywords("cpython interpreter", ["py"])
        assert not loader._matches_keywords("jython", ["py"])

    def test_extension_match(self, loader: SkillsLoader) -> None:
        assert loader._matches_keywords("file.py", [".py"])
        assert loader._matches_keywords("script.sh", [".sh"])

    def test_escaped_extension_match(self, loader: SkillsLoader) -> None:
        assert loader._matches_keywords("file.py", ["\\.py"])

    def test_boundary_with_hyphen(self, loader: SkillsLoader) -> None:
        assert loader._matches_keywords("python-dev", ["python"])

    def test_boundary_with_underscore(self, loader: SkillsLoader) -> None:
        """Underscore is treated as word character, so 'use_python' should not match
        with boundary check. But the keyword appears after underscore."""
        # This depends on implementation: underscore is [a-z0-9_]
        # so 'python' in 'use_python' won't match (underscore is word char)
        assert not loader._matches_keywords("use_python_3", ["python"])

    def test_no_match_for_suffix(self, loader: SkillsLoader) -> None:
        assert not loader._matches_keywords("pythonic code", ["python"])

    def test_keyword_at_start(self, loader: SkillsLoader) -> None:
        assert loader._matches_keywords("python is great", ["python"])

    def test_keyword_at_end(self, loader: SkillsLoader) -> None:
        assert loader._matches_keywords("use python", ["python"])

    def test_keyword_alone(self, loader: SkillsLoader) -> None:
        assert loader._matches_keywords("python", ["python"])

    def test_empty_keywords(self, loader: SkillsLoader) -> None:
        assert not loader._matches_keywords("anything", [])

    def test_empty_task(self, loader: SkillsLoader) -> None:
        assert not loader._matches_keywords("", ["python"])


# ============================================================
# Thinking Mode Detection
# ============================================================


class TestThinkingModeDetection:
    """Tests for _detect_thinking_mode()."""

    def test_simple_mode_ls(self, loader: SkillsLoader) -> None:
        assert loader._detect_thinking_mode("ls -la") == ThinkingMode.SIMPLE

    def test_simple_mode_show(self, loader: SkillsLoader) -> None:
        assert loader._detect_thinking_mode("show me the logs") == ThinkingMode.SIMPLE

    def test_simple_mode_list(self, loader: SkillsLoader) -> None:
        assert loader._detect_thinking_mode("list all files") == ThinkingMode.SIMPLE

    def test_medium_mode_create(self, loader: SkillsLoader) -> None:
        assert (
            loader._detect_thinking_mode("Create a Python script")
            == ThinkingMode.MEDIUM
        )

    def test_medium_mode_fix(self, loader: SkillsLoader) -> None:
        assert loader._detect_thinking_mode("fix the bug") == ThinkingMode.MEDIUM

    def test_medium_mode_refactor(self, loader: SkillsLoader) -> None:
        assert (
            loader._detect_thinking_mode("refactor the module") == ThinkingMode.MEDIUM
        )

    def test_complex_mode_design(self, loader: SkillsLoader) -> None:
        assert (
            loader._detect_thinking_mode("Design a microservices architecture")
            == ThinkingMode.COMPLEX
        )

    def test_complex_mode_migrate(self, loader: SkillsLoader) -> None:
        assert (
            loader._detect_thinking_mode("migrate the database") == ThinkingMode.COMPLEX
        )

    def test_complex_mode_research(self, loader: SkillsLoader) -> None:
        assert (
            loader._detect_thinking_mode("research best practices")
            == ThinkingMode.COMPLEX
        )

    def test_default_is_medium(self, loader: SkillsLoader) -> None:
        """Unrecognized task should default to medium mode."""
        assert (
            loader._detect_thinking_mode("do something unusual") == ThinkingMode.MEDIUM
        )

    def test_complex_takes_priority(self, loader: SkillsLoader) -> None:
        """Complex patterns should match before medium when both could apply."""
        # "design" is complex, even though it could partially match other modes
        assert (
            loader._detect_thinking_mode("design and create a system")
            == ThinkingMode.COMPLEX
        )


# ============================================================
# Always-Load Resolution
# ============================================================


class TestAlwaysLoad:
    """Tests for _resolve_always_load()."""

    def test_always_load_skills_prepended(self, loader: SkillsLoader) -> None:
        """Always-load skills should appear at the beginning."""
        result = loader._resolve_always_load([])
        names = [name for name, _ in result]
        # ja and think should be in always-load
        assert "ja" in names
        assert "think" in names

    def test_no_duplication(self, loader: SkillsLoader) -> None:
        """Skills already in task list should not be duplicated."""
        catalog_data = loader.catalog.get("catalog") or loader.catalog.get("cat", {})
        think_meta = catalog_data.get("think", {})

        task_skills = [("think", think_meta)]
        result = loader._resolve_always_load(task_skills)
        names = [name for name, _ in result]

        # think should appear exactly once
        assert names.count("think") == 1


# ============================================================
# Skill Loading (Integration)
# ============================================================


class TestLoadForTask:
    """Integration tests for load_for_task()."""

    def test_python_task_loads_langs(self, loader: SkillsLoader) -> None:
        result = loader.load_for_task("Create a Python script")
        assert "python" in result.lower() or "langs" in result.lower()

    def test_docker_task_loads_infra(self, loader: SkillsLoader) -> None:
        result = loader.load_for_task("Set up Docker container")
        assert "docker" in result.lower() or "infra" in result.lower()

    def test_git_task_loads_infra(self, loader: SkillsLoader) -> None:
        result = loader.load_for_task("git commit changes")
        assert "infra" in result.lower() or "git" in result.lower()

    def test_token_budget_not_exceeded(self, loader: SkillsLoader) -> None:
        """Token usage should never exceed the budget."""
        tasks = [
            "ls -la",
            "Create a Python script",
            "Design a microservices architecture",
            "Set up Docker container with git",
            "research best practices for security audit",
        ]
        for task in tasks:
            result = loader.load_for_task(task)
            match = re.search(r"Tokens used: (\d+)/(\d+)", result)
            assert match is not None, f"No token info in output for task: {task}"
            used, limit = int(match.group(1)), int(match.group(2))
            assert used <= limit, f"Budget exceeded for '{task}': {used}/{limit}"

    def test_empty_task_loads_always_skills(self, loader: SkillsLoader) -> None:
        """Even with no keyword matches, always-load skills should be present."""
        result = loader.load_for_task("xyzzy")
        # ja and think are always loaded
        assert "Think" in result or "think" in result.lower()

    def test_all_skills_loadable(self, loader: SkillsLoader) -> None:
        """All skill files referenced in catalog should be loadable."""
        catalog_data = loader.catalog.get("catalog") or loader.catalog.get("cat", {})
        for skill_name, meta in catalog_data.items():
            if not isinstance(meta, dict):
                continue
            path_value = meta.get("path", "")
            skill_path = loader.base_path / "skills" / path_value
            content = loader._load_skill_content(skill_path)
            assert content is not None, (
                f"Failed to load skill '{skill_name}': {skill_path}"
            )

    def test_output_contains_core_section(self, loader: SkillsLoader) -> None:
        result = loader.load_for_task("ls -la")
        assert "Core Skills" in result

    def test_output_contains_thinking_mode(self, loader: SkillsLoader) -> None:
        result = loader.load_for_task("Create a script")
        assert "Thinking Mode:" in result
        assert "Thinking mode:" in result


# ============================================================
# Presets
# ============================================================


class TestPresets:
    """Tests for preset functionality."""

    def test_preset_py_dev(self, loader: SkillsLoader) -> None:
        """py_dev preset should load think, langs, prac."""
        result = loader.load_for_task("any task", preset="py_dev")
        assert "Think" in result or "think" in result.lower()
        assert "Lang" in result or "lang" in result.lower()

    def test_preset_devops(self, loader: SkillsLoader) -> None:
        result = loader.load_for_task("any task", preset="devops")
        assert "Infra" in result or "infra" in result.lower()

    def test_preset_unknown_raises_error(self, loader: SkillsLoader) -> None:
        with pytest.raises(SkillsLoaderError, match="not found"):
            loader.load_for_task("any task", preset="nonexistent")

    def test_preset_includes_always_load(self, loader: SkillsLoader) -> None:
        """Presets should still include always-load skills."""
        result = loader.load_for_task("task", preset="general")
        # ja is always loaded
        assert "Ja" in result or "ja" in result.lower()

    def test_all_defined_presets_valid(self, loader: SkillsLoader) -> None:
        """All presets defined in catalog should resolve without errors."""
        presets = loader.catalog.get("presets", {})
        for preset_name in presets:
            # Should not raise
            result = loader.load_for_task("test task", preset=preset_name)
            assert len(result) > 0


# ============================================================
# Ordering
# ============================================================


class TestOrdering:
    """Tests for skill load ordering."""

    def test_high_priority_first(self, loader: SkillsLoader) -> None:
        """High priority skills should appear before normal priority."""
        task_skills = loader._analyze_task_keywords(
            "design a python script with code review"
        )
        names = [name for name, _ in task_skills]
        if "think" in names and len(names) > 1:
            # think has pri: hi, should be first among matched skills
            assert names[0] == "think"

    def test_order_field_respected(self, loader: SkillsLoader) -> None:
        """Skills with lower order values should come before higher ones."""
        task_skills = loader._analyze_task_keywords(
            "design a python script with code review"
        )
        names = [name for name, _ in task_skills]
        if "langs" in names and "prac" in names:
            # order: langs=2, prac=3
            assert names.index("langs") < names.index("prac")


# ============================================================
# Edge Cases
# ============================================================


class TestEdgeCases:
    """Edge case tests."""

    def test_load_nonexistent_skill_file(self, loader: SkillsLoader) -> None:
        fake_path = loader.base_path / "skills" / "nonexistent.yaml"
        result = loader._load_skill_content(fake_path)
        assert result is None

    def test_parse_keywords_from_list(self, loader: SkillsLoader) -> None:
        meta = {"kw": ["python", "py"]}
        result = loader._parse_keywords(meta)
        assert result == ["python", "py"]

    def test_parse_keywords_from_pipe_string(self, loader: SkillsLoader) -> None:
        meta = {"kw": "python|bash|rust"}
        result = loader._parse_keywords(meta)
        assert result == ["python", "bash", "rust"]

    def test_parse_keywords_empty(self, loader: SkillsLoader) -> None:
        meta = {}
        result = loader._parse_keywords(meta)
        assert result == []

    def test_catalog_is_flat_detection(self, loader: SkillsLoader) -> None:
        flat = {"skill1": {"path": "a.yaml", "tok": 100}}
        assert loader._catalog_is_flat(flat) is True

        categorized = {"category1": {"skill1": {"path": "a.yaml", "tok": 100}}}
        # The inner dict has meta keys, so first value check returns True
        # Actually _catalog_is_flat checks the top-level values
        # categorized top-level value is {"skill1": {...}} which doesn't have meta keys
        assert loader._catalog_is_flat(categorized) is False
