"""Output formatting for skills loader."""

from typing import Dict, List, Optional, Tuple

import yaml


class SkillsFormatter:
    """Handles output formatting for loaded skills."""

    def __init__(self, catalog: Dict):
        self._catalog = catalog

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Estimate token count from text content.

        Uses a heuristic: 4 chars per token for English-dominant text,
        3 chars per token when Japanese characters exceed 30%.
        """
        if not text:
            return 0
        total_chars = len(text)
        japanese_chars = sum(1 for c in text if ord(c) > 0x3000)
        if japanese_chars > total_chars * 0.3:
            return max(1, total_chars // 3)
        else:
            return max(1, total_chars // 4)

    def format_thinking_header(self, mode: str) -> str:
        """Format thinking mode header for output."""
        mode_config_root = self._catalog.get(
            "thinking_mode_auto_detect"
        ) or self._catalog.get("think_mode", {})
        mode_config = mode_config_root.get(mode, {})
        overhead = mode_config.get("overhead_budget") or mode_config.get("budget", "?")
        return (
            f"\n# Thinking Mode: {mode.upper()}\n# Overhead budget: {overhead} tokens\n"
        )

    def format_output(
        self,
        core_content: str,
        thinking_mode: str,
        skills: List[Tuple[str, str, Optional[Dict]]],
        tokens_used: int,
        max_tokens: int,
    ) -> str:
        """Format the final output with core, skills, and metadata."""
        output = ["# Core Skills (Always Loaded)\n"]
        output.append(core_content)
        output.append(self.format_thinking_header(thinking_mode))

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
