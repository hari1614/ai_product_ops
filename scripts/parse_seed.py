import re
import json
from pathlib import Path

def parse_task_md():
    task_file = Path("d:/projects/poc/ai_ops/task.md")
    content = task_file.read_text(encoding="utf-8")
    
    # Categories regex
    category_pattern = re.compile(r'^\d+\.\s+(.+)$', re.MULTILINE)
    
    # Split content by category sections
    lines = content.splitlines()
    
    categories = []
    current_category = None
    apps = []
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        cat_match = re.match(r'^(\d+)\.\s+([A-Za-z0-9,\s&/_-]+)$', line)
        if cat_match and not line.startswith('#'):
            cat_num = int(cat_match.group(1))
            cat_name = cat_match.group(2).strip()
            if 1 <= cat_num <= 10:
                current_category = f"{cat_num}. {cat_name}"
                i += 1
                continue
                
        # Check if line is a number (app index)
        if line.isdigit() and current_category:
            app_id = int(line)
            if 1 <= app_id <= 100 and i + 2 < len(lines):
                # Next line is app name
                app_name = lines[i+1].strip()
                # Next line is website / hint
                hint = lines[i+2].strip()
                
                apps.append({
                    "id": app_id,
                    "name": app_name,
                    "category": current_category,
                    "hint_url": hint
                })
                i += 3
                continue
        i += 1

    print(f"Parsed {len(apps)} apps across categories.")
    
    out_dir = Path("d:/projects/poc/ai_ops/data")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    out_file = out_dir / "apps_seed.json"
    out_file.write_text(json.dumps(apps, indent=2), encoding="utf-8")
    print(f"Wrote to {out_file}")

if __name__ == "__main__":
    parse_task_md()
