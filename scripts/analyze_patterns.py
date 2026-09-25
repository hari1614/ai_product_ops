import json
import csv
from pathlib import Path
from collections import Counter, defaultdict

def analyze_dataset():
    data_file = Path("d:/projects/poc/ai_ops/data/pass2_verified.json")
    if not data_file.exists():
        data_file = Path("d:/projects/poc/ai_ops/data/pass1_research_raw.json")
    
    if not data_file.exists():
        print("No research dataset found to analyze.")
        return

    apps = json.loads(data_file.read_text(encoding="utf-8"))
    total_apps = len(apps)

    # 1. Auth Distribution
    auth_counter = Counter()
    for app in apps:
        for auth in app.get("auth_methods", []):
            auth_clean = auth.strip()
            if "oauth" in auth_clean.lower():
                auth_counter["OAuth2"] += 1
            elif "api key" in auth_clean.lower() or "apikey" in auth_clean.lower():
                auth_counter["API Key"] += 1
            elif "bearer" in auth_clean.lower() or "token" in auth_clean.lower() or "pat" in auth_clean.lower():
                auth_counter["Personal Access Token / Bearer"] += 1
            elif "basic" in auth_clean.lower():
                auth_counter["Basic Auth"] += 1
            elif "cookie" in auth_clean.lower() or "session" in auth_clean.lower():
                auth_counter["Session Cookie / Reverse Eng"] += 1
            else:
                auth_counter[auth_clean] += 1

    # 2. Gating Distribution
    gating_counter = Counter()
    for app in apps:
        g = app.get("gating_type", "Unknown")
        gating_counter[g] += 1

    # 3. Verdict Distribution
    verdict_counter = Counter()
    for app in apps:
        v = app.get("buildability_verdict", "Unknown")
        verdict_counter[v] += 1

    # 4. MCP Status
    mcp_counter = Counter()
    for app in apps:
        m = app.get("mcp_status", "None")
        mcp_counter[m] += 1

    # 5. Category Breakdown
    cat_breakdown = defaultdict(lambda: {
        "count": 0,
        "self_serve": 0,
        "gated": 0,
        "ready_today": 0,
        "oauth_count": 0,
        "api_key_count": 0
    })

    for app in apps:
        cat = app.get("category", "General")
        cat_breakdown[cat]["count"] += 1
        
        gating = app.get("gating_type", "")
        if "self-serve" in gating.lower() or "free" in gating.lower():
            cat_breakdown[cat]["self_serve"] += 1
        else:
            cat_breakdown[cat]["gated"] += 1
            
        verdict = app.get("buildability_verdict", "")
        if "ready" in verdict.lower():
            cat_breakdown[cat]["ready_today"] += 1
            
        auths = " ".join(app.get("auth_methods", [])).lower()
        if "oauth" in auths:
            cat_breakdown[cat]["oauth_count"] += 1
        if "api key" in auths or "apikey" in auths:
            cat_breakdown[cat]["api_key_count"] += 1

    # 6. Easy Wins vs Outreach Required
    easy_wins = [app for app in apps if app.get("easy_win_score", 0) >= 8 and "ready" in app.get("buildability_verdict", "").lower()]
    enterprise_outreach = [app for app in apps if "partner" in app.get("gating_type", "").lower() or "enterprise" in app.get("gating_type", "").lower() or "partner" in app.get("buildability_verdict", "").lower()]

    summary = {
        "total_apps": total_apps,
        "auth_distribution": dict(auth_counter.most_common()),
        "gating_distribution": dict(gating_counter.most_common()),
        "verdict_distribution": dict(verdict_counter.most_common()),
        "mcp_distribution": dict(mcp_counter.most_common()),
        "category_breakdown": dict(cat_breakdown),
        "easy_wins_count": len(easy_wins),
        "enterprise_outreach_count": len(enterprise_outreach),
        "easy_win_examples": [{"id": a["id"], "name": a["name"], "category": a["category"]} for a in easy_wins[:10]],
        "enterprise_outreach_examples": [{"id": a["id"], "name": a["name"], "blocker": a.get("main_blocker", "")} for a in enterprise_outreach[:10]]
    }

    out_dir = Path("d:/projects/poc/ai_ops/data")
    summary_file = out_dir / "summary_insights.json"
    summary_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    # Export to CSV
    csv_file = out_dir / "final_research_100_apps.csv"
    if apps:
        keys = ["id", "name", "category", "one_liner", "auth_methods", "gating_type", "api_surface", "mcp_status", "buildability_verdict", "main_blocker", "evidence_url", "easy_win_score"]
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(keys)
            for app in apps:
                writer.writerow([
                    app.get("id"),
                    app.get("name"),
                    app.get("category"),
                    app.get("one_liner"),
                    ", ".join(app.get("auth_methods", [])) if isinstance(app.get("auth_methods"), list) else app.get("auth_methods"),
                    app.get("gating_type"),
                    app.get("api_surface"),
                    app.get("mcp_status"),
                    app.get("buildability_verdict"),
                    app.get("main_blocker"),
                    app.get("evidence_url"),
                    app.get("easy_win_score")
                ])
        print(f"Exported CSV dataset to {csv_file}")
    
    print("Pattern analysis complete! Insights saved to summary_insights.json")

if __name__ == "__main__":
    analyze_dataset()
