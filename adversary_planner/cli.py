"""CLI entry point for Adversary Planner."""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from .campaign import CampaignManager
from .importer import import_garak_report
from .reporter import generate_report
from .catalog import get_techniques, FAMILIES, get_technique

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="adversary-planner")
def main():
    """Adversary Planner — Bayesian attack planning for LLM security.

    Turn garak scan results into adaptive red team campaigns with
    Thompson Sampling, Z-score calibration, and compliance mapping.
    """


# ── campaign ───────────────────────────────────────────────────────────────


@main.group()
def campaign():
    """Manage red team campaigns."""


@campaign.command("new")
@click.argument("target_file", type=click.Path(exists=True))
@click.option("--name", "-n", required=True, help="Campaign name")
@click.option("--adaptive/--static", default=True, help="Enable Bayesian adaptive planner")
@click.option("--dir", "base_dir", default=None, help="Campaign storage directory")
def campaign_new(target_file: str, name: str, adaptive: bool, base_dir: str | None):
    """Create a new campaign from a target YAML file."""
    mgr = CampaignManager(Path(base_dir) if base_dir else None)
    state = mgr.create(target_file, name, adaptive)

    console.print(Panel(
        f"[bold green]Campaign created successfully[/]\n\n"
        f"  ID:       [cyan]{state.id}[/]\n"
        f"  Name:     {state.name}\n"
        f"  Target:   {state.target.get('name', 'Unknown')}\n"
        f"  Adaptive: {'Yes' if state.adaptive else 'No'}\n"
        f"  Phase:    {mgr.get_phase().title()}\n\n"
        f"Next: run [bold]aplanner campaign next {state.id}[/] to get recommendations",
        title="New Campaign",
    ))


@campaign.command("list")
@click.option("--dir", "base_dir", default=None, help="Campaign storage directory")
def campaign_list(base_dir: str | None):
    """List all campaigns."""
    mgr = CampaignManager(Path(base_dir) if base_dir else None)
    campaigns = mgr.list_campaigns()

    if not campaigns:
        console.print("[yellow]No campaigns found.[/]")
        return

    table = Table(title="Campaigns")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Target")
    table.add_column("Rounds", justify="right")
    table.add_column("Status")
    table.add_column("Created")

    for c in campaigns:
        status_style = "green" if c["status"] == "active" else "dim"
        table.add_row(
            c["id"], c["name"], c["target"],
            str(c["rounds"]),
            f"[{status_style}]{c['status']}[/]",
            c["created"][:10],
        )

    console.print(table)


@campaign.command("next")
@click.argument("campaign_id")
@click.option("--count", "-c", default=5, help="Number of recommendations")
@click.option("--no-diversify", is_flag=True, help="Allow multiple techniques per family")
@click.option("--dir", "base_dir", default=None, help="Campaign storage directory")
def campaign_next(campaign_id: str, count: int, no_diversify: bool, base_dir: str | None):
    """Get next technique recommendations for a campaign."""
    mgr = CampaignManager(Path(base_dir) if base_dir else None)
    mgr.load(campaign_id)

    phase = mgr.get_phase()
    recs = mgr.next_recommendations(count=count, diversify=not no_diversify)

    console.print(f"\n[bold]Campaign:[/] {mgr.state.name}  |  "
                  f"[bold]Phase:[/] {phase.title()}  |  "
                  f"[bold]Rounds:[/] {len(mgr.state.rounds)}\n")

    table = Table(title=f"Top {count} Recommended Techniques")
    table.add_column("#", justify="right", style="bold")
    table.add_column("Technique", style="cyan")
    table.add_column("Family")
    table.add_column("Score", justify="right")
    table.add_column("Mean", justify="right")
    table.add_column("±Uncertainty", justify="right")
    table.add_column("Rationale")

    for i, rec in enumerate(recs, 1):
        table.add_row(
            str(i),
            rec.technique_name,
            rec.family,
            f"{rec.sampled_score:.3f}",
            f"{rec.posterior_mean:.1%}",
            f"±{rec.uncertainty:.1%}",
            rec.reason,
        )

    console.print(table)

    console.print("\n[bold]Suggested garak commands:[/]\n")
    for rec in recs:
        if rec.suggested_probes:
            for probe in rec.suggested_probes:
                console.print(f"  garak --model_type <type> --model_name <name> --probes {probe}")

    console.print(f"\n[dim]After scanning, import results with: "
                  f"aplanner import garak {campaign_id} <report.jsonl>[/]")


@campaign.command("status")
@click.argument("campaign_id")
@click.option("--dir", "base_dir", default=None, help="Campaign storage directory")
def campaign_status(campaign_id: str, base_dir: str | None):
    """Show detailed campaign status."""
    mgr = CampaignManager(Path(base_dir) if base_dir else None)
    mgr.load(campaign_id)
    state = mgr.state

    tested = mgr.get_tested_technique_ids()
    phase = mgr.get_phase()

    console.print(Panel(
        f"  [bold]ID:[/]       {state.id}\n"
        f"  [bold]Name:[/]     {state.name}\n"
        f"  [bold]Target:[/]   {state.target.get('name', 'Unknown')}\n"
        f"  [bold]Phase:[/]    {phase.title()}\n"
        f"  [bold]Rounds:[/]   {len(state.rounds)}\n"
        f"  [bold]Tested:[/]   {len(tested)} / 49 techniques\n"
        f"  [bold]Status:[/]   {state.status}\n"
        f"  [bold]Created:[/]  {state.created[:10]}\n"
        f"  [bold]Updated:[/]  {state.updated[:10]}",
        title="Campaign Status",
    ))

    if state.rounds:
        table = Table(title="Round History")
        table.add_column("Round", justify="right")
        table.add_column("Date")
        table.add_column("Source")
        table.add_column("Techniques", justify="right")
        table.add_column("Successes", justify="right", style="red")
        table.add_column("Failures", justify="right", style="green")

        for rd in state.rounds:
            table.add_row(
                str(rd["round_number"]),
                rd["timestamp"][:10],
                rd["source"],
                str(len(rd["techniques_updated"])),
                str(rd["total_successes"]),
                str(rd["total_failures"]),
            )

        console.print(table)


# ── import ─────────────────────────────────────────────────────────────────


@main.group("import")
def import_cmd():
    """Import scan results from external tools."""


@import_cmd.command("garak")
@click.argument("campaign_id")
@click.argument("report_file", type=click.Path(exists=True))
@click.option("--dir", "base_dir", default=None, help="Campaign storage directory")
def import_garak(campaign_id: str, report_file: str, base_dir: str | None):
    """Import garak JSONL report into a campaign."""
    mgr = CampaignManager(Path(base_dir) if base_dir else None)
    mgr.load(campaign_id)

    console.print(f"[bold]Importing:[/] {report_file}")
    result = import_garak_report(report_file)

    console.print(f"  Attempts parsed:   {result.total_attempts}")
    console.print(f"  Mapped to techs:   {result.total_mapped}")
    console.print(f"  Techniques hit:    {len(result.technique_results)}")

    if result.unmapped_probes:
        console.print(f"  [yellow]Unmapped probes:   {len(result.unmapped_probes)}[/]")
        for p in result.unmapped_probes[:5]:
            console.print(f"    - {p}")

    record = mgr.import_results(result)

    console.print(Panel(
        f"[bold green]Round {record.round_number} recorded[/]\n\n"
        f"  Successes: [red]{record.total_successes}[/]\n"
        f"  Failures:  [green]{record.total_failures}[/]\n"
        f"  Techniques updated: {len(record.techniques_updated)}\n\n"
        f"Next: run [bold]aplanner campaign next {campaign_id}[/] for updated recommendations",
        title="Import Complete",
    ))


# ── report ─────────────────────────────────────────────────────────────────


@main.command()
@click.argument("campaign_id")
@click.option("--output", "-o", default=None, help="Output file path (default: stdout)")
@click.option("--dir", "base_dir", default=None, help="Campaign storage directory")
def report(campaign_id: str, output: str | None, base_dir: str | None):
    """Generate a campaign report."""
    mgr = CampaignManager(Path(base_dir) if base_dir else None)
    mgr.load(campaign_id)

    report_text = generate_report(mgr, output)

    if output:
        console.print(f"[bold green]Report saved to:[/] {output}")
    else:
        console.print(report_text)


# ── techniques ─────────────────────────────────────────────────────────────


@main.command()
@click.option("--family", "-f", default=None, help="Filter by technique family")
def techniques(family: str | None):
    """List all techniques in the catalog."""
    techs = get_techniques()

    if family:
        techs = [t for t in techs if t.family == family]
        if not techs:
            console.print(f"[yellow]No techniques found in family: {family}[/]")
            console.print(f"Available families: {', '.join(sorted(FAMILIES.keys()))}")
            return

    table = Table(title="Technique Catalog")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="bold")
    table.add_column("Family")
    table.add_column("ATLAS", style="dim")
    table.add_column("OWASP")
    table.add_column("garak Probes")

    for t in techs:
        owasp = ", ".join(t.owasp_categories) if t.owasp_categories else "-"
        probes = ", ".join(t.garak_probes) if t.garak_probes else "[dim]-[/]"
        table.add_row(
            t.id, t.name, t.family,
            t.atlas_technique or "-",
            owasp, probes,
        )

    console.print(table)
    console.print(f"\n[dim]{len(techs)} techniques across {len(set(t.family for t in techs))} families[/]")


@main.command()
def families():
    """List all technique families."""
    table = Table(title="Technique Families")
    table.add_column("Family", style="cyan bold")
    table.add_column("Description")
    table.add_column("Techniques", justify="right")

    all_techs = get_techniques()
    for fam, desc in sorted(FAMILIES.items()):
        count = sum(1 for t in all_techs if t.family == fam)
        table.add_row(fam, desc, str(count))

    console.print(table)


if __name__ == "__main__":
    main()
