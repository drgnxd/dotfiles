from pathlib import Path

from skills_loader import SkillsLoader


def test_skills_catalog_validation_passes() -> None:
    base_path = Path(__file__).resolve().parents[1]
    loader = SkillsLoader(base_path=base_path)
    errors = loader.validate_catalog()
    assert errors == []
