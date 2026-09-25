import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

load_dotenv()
console = Console()

async def main():
    console.print(Panel.fit(
        "[bold cyan]Composio AI Product Ops — 100 Apps Research & Verification Agent[/bold cyan]\n"
        "[white]Autonomous Research Pipeline, Verification Critic, Pattern Synthesis & Accuracy Tracking[/white]",
        border_style="cyan"
    ))

    # Step 1: Ingest seed
    console.print("\n[bold yellow]Step 1/5: Parsing Seed Data from task.md...[/bold yellow]")
    from parse_seed import parse_task_md
    parse_task_md()

    # Step 2: Check OpenRouter key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        console.print("[bold red]Missing OPENROUTER_API_KEY in .env![/bold red]")
        console.print("Please open d:/projects/poc/ai_ops/.env and add your OpenRouter API key.")
        return

    # Step 3: Run Pass 1 Research Agent
    console.print("\n[bold yellow]Step 2/5: Running Pass 1 Autonomous Extraction Agent...[/bold yellow]")
    from research_agent import run_pass1_research
    await run_pass1_research()

    # Step 4: Run Pass 2 Verification Critic & URL Liveness Loop
    console.print("\n[bold yellow]Step 3/5: Running Pass 2 Verification Critic Loop...[/bold yellow]")
    from verify_agent import run_pass2_verification
    await run_pass2_verification()

    # Step 5: Run Sample Audit & Accuracy Progression
    console.print("\n[bold yellow]Step 4/5: Calculating Accuracy Progression & Sample Audit...[/bold yellow]")
    from sample_audit import compute_accuracy_progression
    compute_accuracy_progression()

    # Step 6: Analyze Macro Patterns & Export Final Datasets
    console.print("\n[bold yellow]Step 5/5: Synthesizing Macro Patterns & Exporting Final Results...[/bold yellow]")
    from analyze_patterns import analyze_dataset
    analyze_dataset()

    console.print(Panel.fit(
        "[bold green]Pipeline Execution Completed Successfully![/bold green]\n"
        "[white]1. Raw Pass 1 Data: data/pass1_research_raw.json\n"
        "2. Verified Pass 2 Data: data/pass2_verified.json\n"
        "3. Accuracy Audit: data/accuracy_audit.json\n"
        "4. Summary Insights: data/summary_insights.json\n"
        "5. Final Export: data/final_research_100_apps.csv[/white]",
        border_style="green"
    ))

if __name__ == "__main__":
    asyncio.run(main())
