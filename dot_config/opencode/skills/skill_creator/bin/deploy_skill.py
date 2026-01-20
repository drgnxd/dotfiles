import os
import sys
from pathlib import Path

def deploy_skill(skill_name: str, base_path: str = "dot_config/opencode/skills"):
    """
    Safely creates a new skill directory structure.
    Adheres to AGENTS.md File Safety and Directory Navigation rules.
    """
    target_dir = Path(base_path) / skill_name
    sub_dirs = ["bin", "refs"]

    # Verify CWD
    print(f"[DEBUG] Current Working Directory: {os.getcwd()}")
    
    if target_dir.exists():
        print(f"Error: Skill '{skill_name}' already exists. Overwrite denied without manual intervention.")
        sys.exit(1)

    try:
        # Create directories
        for sd in sub_dirs:
            (target_dir / sd).mkdir(parents=True, exist_ok=True)
        
        # Initialize SKILL.md with inheritance header
        with open(target_dir / "SKILL.md", "w") as f:
            f.write(f"# SKILL: {skill_name}\n> **INHERITANCE:** Strictly adheres to /dot_config/opencode/AGENTS.md\n")
            
        print(f"Successfully deployed structure for: {skill_name}")
        print(f"Path: {target_dir}")
        
    except Exception as e:
        print(f"Deployment failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 deploy_skill.py <skill_name_in_snake_case>")
        sys.exit(1)
    deploy_skill(sys.argv[1])
