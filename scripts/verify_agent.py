import os
import json
import asyncio
import aiohttp
from pathlib import Path
from dotenv import load_dotenv
from openai import AsyncOpenAI
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn

load_dotenv()
console = Console()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
CONCURRENCY = int(os.getenv("CONCURRENCY", "5"))

VERIFIER_PROMPT = """You are an expert Chief Verification Architect for Composio toolkits and MCP integrations.
Your job is to rigorously CRITIQUE and VERIFY the initial research data collected for a SaaS application.

Initial Research Input:
{initial_data}

Verified Docs URL Status: {url_status} (HTTP {status_code})

Tasks:
1. Verify if the Auth Methods are 100% accurate (e.g. check if OAuth2 vs API key vs Personal Access Token).
2. Check Gating Type: Is it genuinely self-serve free/trial or is it behind a paid plan, enterprise contract, or partner approval (e.g. PitchBook, DealCloud, Salesforce Commerce Cloud)?
3. Check MCP status: Does an official MCP server, community MCP server, or Composio connector exist?
4. Review Buildability Verdict: Is it "Ready Today", "Blocked: Partner Gate", "Blocked: Enterprise Only", "Blocked: No Public API", or "Community Wrapper Required"?
5. Review Evidence URL: If the initial URL is generic (e.g. just the root domain), replace it with the exact direct developer documentation / API reference URL.
6. Provide a 'verification_status': 'Verified Unchanged' or 'Corrected & Enhanced'.
7. Provide 'corrections_made': List of specific corrections made or 'None'.
8. Provide 'confidence_score': 0-100 score on data integrity.

Return the final verified app data as a valid JSON object matching the full schema with all fields."""

async def check_url_liveness(session: aiohttp.ClientSession, url: str) -> tuple[bool, int]:
    if not url.startswith("http"):
        url = "https://" + url
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=6), allow_redirects=True) as resp:
            return (resp.status < 400, resp.status)
    except Exception:
        return (False, 0)

async def verify_single_app(client: AsyncOpenAI, session: aiohttp.ClientSession, app: dict, semaphore: asyncio.Semaphore) -> dict:
    async with semaphore:
        is_live, status_code = await check_url_liveness(session, app.get("evidence_url", app.get("hint_url", "")))
        url_status = "Live and Accessible" if is_live else "Unreachable or Gated"
        
        prompt = VERIFIER_PROMPT.format(
            initial_data=json.dumps(app, indent=2),
            url_status=url_status,
            status_code=status_code
        )

        for attempt in range(3):
            try:
                response = await client.chat.completions.create(
                    model=OPENROUTER_MODEL,
                    messages=[
                        {"role": "system", "content": "You are a meticulous developer relations verification auditor. Output valid JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1
                )
                
                content = response.choices[0].message.content
                data = json.loads(content)
                # Keep ID and basic fields intact
                data["id"] = app["id"]
                data["name"] = app["name"]
                data["category"] = app["category"]
                data["url_http_status"] = status_code
                return data
            except Exception as e:
                if attempt == 2:
                    app["verification_status"] = "Verification Fallback"
                    app["corrections_made"] = [f"Verification error: {e}"]
                    app["confidence_score"] = 75
                    app["url_http_status"] = status_code
                    return app
                await asyncio.sleep(2 ** attempt)

async def run_pass2_verification():
    if not OPENROUTER_API_KEY:
        console.print("[bold red]Error: OPENROUTER_API_KEY is not set in .env[/bold red]")
        return

    pass1_file = Path("d:/projects/poc/ai_ops/data/pass1_research_raw.json")
    if not pass1_file.exists():
        console.print("[red]Pass 1 output file not found. Run research_agent.py first.[/red]")
        return

    pass1_data = json.loads(pass1_file.read_text(encoding="utf-8"))
    console.print(f"[bold cyan]Starting Pass 2 Verification Loop across {len(pass1_data)} apps...[/bold cyan]")

    client = AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
        default_headers={"HTTP-Referer": "https://composio.dev", "X-Title": "Composio Verification Agent"}
    )

    connector = aiohttp.TCPConnector(limit=CONCURRENCY * 2, ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        semaphore = asyncio.Semaphore(CONCURRENCY)
        tasks = [verify_single_app(client, session, app, semaphore) for app in pass1_data]

        verified_results = []
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            task_tracker = progress.add_task("[green]Verifying and cross-checking apps...", total=len(tasks))
            for coro in asyncio.as_completed(tasks):
                res = await coro
                verified_results.append(res)
                progress.update(task_tracker, advance=1)

    verified_results.sort(key=lambda x: x["id"])

    out_file = Path("d:/projects/poc/ai_ops/data/pass2_verified.json")
    out_file.write_text(json.dumps(verified_results, indent=2), encoding="utf-8")
    console.print(f"[bold green]Pass 2 Complete! Saved verified dataset to {out_file}[/bold green]")

if __name__ == "__main__":
    asyncio.run(run_pass2_verification())
