import os
import json
import asyncio
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from openai import AsyncOpenAI
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn

# Load environment
load_dotenv()

console = Console()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
CONCURRENCY = int(os.getenv("CONCURRENCY", "5"))

class AppResearchResult(BaseModel):
    id: int
    name: str
    category: str
    hint_url: str
    one_liner: str = Field(description="Clear, concise one-line description of what the product does")
    auth_methods: List[str] = Field(description="Auth schemes supported, e.g., ['OAuth2', 'API Key', 'Bearer Token', 'Basic Auth', 'Session Cookie', 'Webhook Secret']")
    gating_type: str = Field(description="Access model: 'Self-Serve Free/Trial', 'Paid Tier Gate', 'Enterprise/Sales Gate', or 'Partner Application Gate'")
    gating_details: str = Field(description="Detailed explanation of how credentials are obtained")
    api_surface: str = Field(description="API types (REST, GraphQL, gRPC, Webhooks, SDKs) and scope/breadth")
    mcp_status: str = Field(description="'Official MCP', 'Community MCP', 'Composio Native', or 'None'")
    mcp_details: str = Field(description="Details of existing MCP server or agent tools if known")
    buildability_verdict: str = Field(description="'Ready Today', 'Blocked: Partner Gate', 'Blocked: Enterprise Only', 'Blocked: No Public API', 'Blocked: Bot Protection / Scraper Only', or 'Community Wrapper Required'")
    main_blocker: str = Field(description="'None (Ready for Toolkit / MCP)' or specific blocker explanation")
    evidence_url: str = Field(description="Accurate, authoritative developer docs URL or official API reference link")
    easy_win_score: int = Field(description="Score from 1 to 10 (10 = instant self-serve API key/OAuth, 1 = strict enterprise sales approval)")

SYSTEM_PROMPT = """You are an expert AI Product Operations & Developer Platform Architect evaluating 100 SaaS applications for toolkit and Model Context Protocol (MCP) buildability at Composio.

For each app, perform deep research on its developer ecosystem and extract precise, factual details:
1. Category & 1-line product purpose.
2. Authentication methods: OAuth2, API Key, Personal Access Token (PAT), Basic Auth, Session Cookie, Webhook HMAC.
3. Access & Gating:
   - Self-Serve Free/Trial: Anyone can sign up and generate API keys / OAuth apps immediately without paying.
   - Paid Tier Gate: API access is locked behind a paid subscription plan.
   - Enterprise/Sales Gate: Requires talking to sales / enterprise contract to get API access.
   - Partner Application Gate: Requires an approved developer/technology partner application.
4. API Surface: REST, GraphQL, gRPC, Webhooks, CLI/SDK breadth.
5. MCP Server Status: Does an official or community Model Context Protocol (MCP) server or Composio toolkit already exist?
6. Buildability Verdict: Can Composio or an AI agent platform build a connector/toolkit TODAY?
   - Ready Today
   - Blocked: Partner Gate
   - Blocked: Enterprise Only
   - Blocked: No Public API
   - Blocked: Bot Protection / Scraper Only
   - Community Wrapper Required
7. Main Blocker: Concise explanation of the blocker or "None (Ready for Toolkit / MCP)".
8. Evidence URL: Authoritative developer documentation URL (e.g. docs.github.com, developer.spotify.com, api.notion.com, etc.).
9. Easy Win Score: 1-10 rating for agentic toolkit integration ease.

Be rigorous and honest. If an app has no public API or is strictly partner-gated (like DealCloud, PitchBook, or certain Meta/WhatsApp tiers), state it clearly.
"""

async def research_single_app(client: AsyncOpenAI, app: dict, semaphore: asyncio.Semaphore) -> dict:
    async with semaphore:
        prompt = f"""Research this application for Composio Toolkit & MCP integration:
App ID: {app['id']}
App Name: {app['name']}
Category: {app['category']}
Website / Hint: {app['hint_url']}

Provide your complete factual research output as a valid JSON object matching the requested schema."""

        for attempt in range(3):
            try:
                response = await client.chat.completions.create(
                    model=OPENROUTER_MODEL,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1
                )
                
                content = response.choices[0].message.content
                data = json.loads(content)
                # Ensure essential fields
                data["id"] = app["id"]
                data["name"] = app["name"]
                data["category"] = app["category"]
                data["hint_url"] = app["hint_url"]
                return data
            except Exception as e:
                if attempt == 2:
                    console.print(f"[red]Failed researching {app['name']}: {e}[/red]")
                    return {
                        "id": app["id"],
                        "name": app["name"],
                        "category": app["category"],
                        "hint_url": app["hint_url"],
                        "one_liner": "Error fetching data",
                        "auth_methods": ["Unknown"],
                        "gating_type": "Unknown",
                        "gating_details": str(e),
                        "api_surface": "Unknown",
                        "mcp_status": "None",
                        "mcp_details": "",
                        "buildability_verdict": "Blocked: Investigation Needed",
                        "main_blocker": str(e),
                        "evidence_url": f"https://{app['hint_url']}",
                        "easy_win_score": 1
                    }
                await asyncio.sleep(2 ** attempt)

async def run_pass1_research():
    if not OPENROUTER_API_KEY:
        console.print("[bold red]Error: OPENROUTER_API_KEY is not set in .env[/bold red]")
        console.print("Please edit .env and provide your OpenRouter API key.")
        return

    seed_file = Path("d:/projects/poc/ai_ops/data/apps_seed.json")
    if not seed_file.exists():
        console.print("[red]Seed file not found. Run parse_seed.py first.[/red]")
        return

    apps = json.loads(seed_file.read_text(encoding="utf-8"))
    console.print(f"[bold cyan]Starting Pass 1 Autonomous Research across {len(apps)} apps using {OPENROUTER_MODEL}...[/bold cyan]")

    client = AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
        default_headers={"HTTP-Referer": "https://composio.dev", "X-Title": "Composio AI Ops Research Agent"}
    )

    semaphore = asyncio.Semaphore(CONCURRENCY)
    tasks = [research_single_app(client, app, semaphore) for app in apps]

    results = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console
    ) as progress:
        task_tracker = progress.add_task("[cyan]Researching apps...", total=len(tasks))
        for coro in asyncio.as_completed(tasks):
            res = await coro
            results.append(res)
            progress.update(task_tracker, advance=1)

    # Sort by ID
    results.sort(key=lambda x: x["id"])

    out_file = Path("d:/projects/poc/ai_ops/data/pass1_research_raw.json")
    out_file.write_text(json.dumps(results, indent=2), encoding="utf-8")
    console.print(f"[bold green]Pass 1 Complete! Saved {len(results)} app research records to {out_file}[/bold green]")

if __name__ == "__main__":
    asyncio.run(run_pass1_research())
