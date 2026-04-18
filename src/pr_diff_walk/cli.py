#!/usr/bin/env python3
import json
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from pr_diff_walk.service import DiffChainService

app = typer.Typer(
    name="pr-diff-walk",
    help="PR dependency chain analysis with multi-language ecosystem support",
    add_completion=False,
)
console = Console()


def parse_integrations(value: Optional[str]) -> Optional[List[str]]:
    if not value:
        return None
    items = value.replace(",", " ").split()
    return [i.strip().lower() for i in items if i.strip()]


@app.command()
def analyze(
    repo: str = typer.Argument(..., help="Repository in format 'owner/repo'"),
    pr: int = typer.Argument(..., help="PR/MR number"),
    token: Optional[str] = typer.Option(None, "--token", "-t", help="Git provider token"),
    local: Optional[str] = typer.Option(None, "--local", "-l", help="Local repository path"),
    depth: int = typer.Option(8, "--depth", "-d", help="Maximum dependency chain depth"),
    integrations: Optional[str] = typer.Option(None, "--integration", "-i", help="Language integrations (comma/space sep, auto-detected if not specified)"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Git provider: github, gitlab"),
    gitlab_url: Optional[str] = typer.Option(None, "--gitlab-url", help="GitLab instance URL (for self-hosted)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
    format: str = typer.Option("report", "--format", "-f", help="Output format: report, json, data"),
) -> None:
    effective_provider = provider or "github"
    parsed_integrations = parse_integrations(integrations)

    try:
        service = DiffChainService(
            repo_name=repo,
            pr_num=pr,
            github_token=token,
            local_repo_path=local,
            max_depth=depth,
            integrations=parsed_integrations,
            provider=effective_provider,
            gitlab_url=gitlab_url,
        )

        console.print(Panel(f"[bold]Analyzing PR/MR #{pr} in {repo}[/bold]"))
        console.print(f"Provider: [cyan]{effective_provider}[/cyan]")
        if parsed_integrations:
            console.print(f"Integrations: [cyan]{', '.join(parsed_integrations)}[/cyan]")
        else:
            console.print("[dim]Integrations: auto-detected from PR files[/dim]")

        result = service.analyze()

        if format == "json":
            output_data = {
                "repo_name": result.repo_name,
                "pr_num": result.pr_num,
                "head_ref": result.head_ref,
                "base_ref": result.base_ref,
                "provider": effective_provider,
                "integrations": result.integration_name,
                "chains": [
                    {
                        "seed": {"file": c.seed.file_path, "name": c.seed.name, "kind": c.seed.kind},
                        "hops": [
                            {
                                "depth": h.depth,
                                "from": {"file": h.from_entity.file_path, "name": h.from_entity.name},
                                "importer": h.importer_file,
                                "imported_as": h.imported_as,
                                "line": h.line_no,
                                "context": h.context_name,
                            }
                            for h in c.hops
                        ],
                    }
                    for c in result.chains
                ],
            }
            json_output = json.dumps(output_data, indent=2)
            if output:
                Path(output).write_text(json_output)
                console.print(f"[green]Output written to {output}[/green]")
            else:
                console.print(json_output)
        elif format == "data":
            output_data = {
                "repo_name": result.repo_name,
                "pr_num": result.pr_num,
                "head_ref": result.head_ref,
                "base_ref": result.base_ref,
                "provider": effective_provider,
                "integrations": result.integration_name,
                "chain_count": len(result.chains),
            }
            json_output = json.dumps(output_data, indent=2)
            if output:
                Path(output).write_text(json_output)
                console.print(f"[green]Output written to {output}[/green]")
            else:
                console.print(json_output)
        else:
            report = service.generate_report(result)
            if output:
                Path(output).write_text(report)
                console.print(f"[green]Report written to {output}[/green]")
            else:
                syntax = Syntax(report, "markdown", theme="monokai", line_numbers=True)
                console.print(syntax)

        console.print(f"\n[bold green]Analysis complete![/bold green]")
        console.print(f"Found [cyan]{len(result.chains)}[/cyan] dependency chains")
        console.print(f"Detected integrations: [cyan]{result.integration_name}[/cyan]")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command(name="list")
def list_integrations() -> None:
    table = Table(title="Available Language Integrations")
    table.add_column("Name", style="cyan")
    table.add_column("Languages", style="green")
    table.add_column("Extensions", style="yellow")

    integration_details = {
        "javascript": ("JavaScript", ".js, .jsx"),
        "typescript": ("TypeScript", ".ts, .tsx"),
        "html": ("HTML", ".html"),
        "css": ("CSS", ".css"),
        "python": ("Python", ".py"),
        "rust": ("Rust", ".rs"),
        "golang": ("Go", ".go"),
        "java": ("Java", ".java"),
        "csharp": ("C#", ".cs"),
        "dart": ("Dart/Flutter", ".dart"),
        "swift": ("Swift", ".swift"),
        "kotlin": ("Kotlin", ".kt, .kts"),
        "c": ("C", ".c, .h"),
        "cpp": ("C++", ".cpp, .cc, .cxx, .hpp, .h"),
        "zig": ("Zig", ".zig"),
        "php": ("PHP", ".php"),
    }

    for name, (langs, exts) in integration_details.items():
        table.add_row(name, langs, exts)

    console.print(table)
    console.print("\n[dim]Multiple integrations are auto-detected from PR files.[/dim]")


@app.command()
def report(
    repo: str = typer.Argument(..., help="Repository in format 'owner/repo'"),
    pr: int = typer.Argument(..., help="PR/MR number"),
    token: Optional[str] = typer.Option(None, "--token", "-t", help="Git provider token"),
    local: Optional[str] = typer.Option(None, "--local", "-l", help="Local repository path"),
    depth: int = typer.Option(8, "--depth", "-d", help="Maximum dependency chain depth"),
    integrations: Optional[str] = typer.Option(None, "--integration", "-i", help="Language integrations (comma/space sep)"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Git provider: github, gitlab"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path (default: stdout)"),
) -> None:
    effective_provider = provider or "github"
    parsed_integrations = parse_integrations(integrations)

    try:
        service = DiffChainService(
            repo_name=repo,
            pr_num=pr,
            github_token=token,
            local_repo_path=local,
            max_depth=depth,
            integrations=parsed_integrations,
            provider=effective_provider,
        )

        result = service.analyze()
        report_text = service.generate_report(result)

        if output:
            Path(output).write_text(report_text)
            console.print(f"[green]Report written to {output}[/green]")
        else:
            syntax = Syntax(report_text, "markdown", theme="monokai", line_numbers=True)
            console.print(syntax)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def quick(
    repo: str = typer.Argument(..., help="Repository in format 'owner/repo'"),
    pr: int = typer.Argument(..., help="PR/MR number"),
    token: Optional[str] = typer.Option(None, "--token", "-t", help="Git provider token"),
    integrations: Optional[str] = typer.Option(None, "--integration", "-i", help="Language integrations (comma/space sep)"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Git provider: github, gitlab"),
) -> None:
    effective_provider = provider or "github"
    parsed_integrations = parse_integrations(integrations)

    try:
        service = DiffChainService(
            repo_name=repo,
            pr_num=pr,
            github_token=token,
            integrations=parsed_integrations,
            provider=effective_provider,
        )

        console.print(f"[bold]Quick analysis for PR/MR #{pr} in {repo}[/bold]")

        result = service.analyze()

        table = Table(title="Dependency Chains Summary")
        table.add_column("Chain", style="cyan")
        table.add_column("Seed Entity", style="green")
        table.add_column("File", style="yellow")
        table.add_column("Hops", style="magenta")

        for idx, chain in enumerate(result.chains, start=1):
            seed = chain.seed
            hop_count = len(chain.hops)
            table.add_row(
                str(idx),
                f"{seed.name} ({seed.kind})",
                seed.file_path,
                str(hop_count),
            )

        console.print(table)
        console.print(f"\n[bold]Total chains:[/bold] {len(result.chains)}")
        console.print(f"[bold]Integrations:[/bold] {result.integration_name}")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)


def main():
    app()


if __name__ == "__main__":
    main()
