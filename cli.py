#!/usr/bin/env python3
"""
CLI entry point for SEO CTR Self-Evolving Agent.
"""

import click
from pathlib import Path
from seo_agent import gsc_client, opportunity


@click.group()
def cli():
    """SEO CTR Self-Evolving Agent CLI."""
    pass


@cli.group()
def gsc():
    """Google Search Console commands."""
    pass


@gsc.command()
@click.option(
    "--site-url", default="https://meetspot-irq2.onrender.com/", help="GSC site URL"
)
@click.option("--days", default=90, help="Number of days to sync")
def sync(site_url, days):
    """Sync GSC data to local parquet cache."""
    click.echo(f"Syncing {days} days of data for {site_url}...")
    gsc_client.sync(site_url, days=days)
    click.echo("✓ Sync complete")


@gsc.command()
@click.option(
    "--site-url", default="https://meetspot-irq2.onrender.com/", help="GSC site URL"
)
def status(site_url):
    """Show sync status."""
    stats = gsc_client.status()
    click.echo(f"Site: {site_url}")
    click.echo(f"Date range: {stats['start_date']} to {stats['end_date']}")
    click.echo(f"Total rows: {stats['rows']:,}")
    click.echo(f"Files: {stats['files']}")


@cli.group()
def opportunities():
    """Opportunity identification commands."""
    pass


@opportunities.command(name="list")
@click.option(
    "--site-url", default="https://meetspot-irq2.onrender.com/", help="GSC site URL"
)
@click.option("--top", default=20, help="Number of top opportunities to show")
@click.option("--min-impressions", default=5, help="Minimum impressions threshold")
@click.option("--position-max", default=50, help="Maximum position to consider")
def list_opportunities(site_url, top, min_impressions, position_max):
    """List top opportunities."""
    df = gsc_client.load_data()
    opps = opportunity.identify_opportunities(
        df, top_n=top, min_impressions=min_impressions, position_range=(1, position_max)
    )

    click.echo(f"\nTop {len(opps)} opportunities:\n")
    for i, opp in enumerate(opps, 1):
        click.echo(f"{i}. {opp['page']}")
        click.echo(f"   Query: {opp['query']}")
        click.echo(
            f"   Position: {opp['position']:.1f} | CTR: {opp['ctr']:.2%} (baseline: {opp['baseline_ctr']:.2%})"
        )
        click.echo(
            f"   Impressions: {opp['impressions']:,} | Opportunity Score: {opp['opportunity_score']:.0f}"
        )
        click.echo()


@cli.command()
@click.argument("page_url")
@click.option("--skill", default="curiosity_gap", help="Skill to use")
def generate(page_url, skill):
    """Generate title/description for a page."""
    from seo_agent import executor

    # Load current data to get context
    df = gsc_client.load_data()
    page_data = df[df["page"] == page_url]

    if page_data.empty:
        click.echo(f"Error: No data found for {page_url}")
        return

    # Get top query for this page
    top_query = page_data.nlargest(1, "impressions").iloc[0]

    result = executor.generate_title_desc(
        page_url=page_url,
        current_title="",  # TODO: fetch from page
        current_desc="",
        query=top_query["query"],
        position=top_query["position"],
        skill_name=skill,
    )

    click.echo(f"\nGenerated with skill: {skill}")
    click.echo(f"Title: {result['title']}")
    click.echo(f"Description: {result['description']}")


@cli.group()
def evolve():
    """Evolution engine commands."""
    pass


@evolve.command()
@click.option(
    "--site-url", default="https://meetspot-irq2.onrender.com/", help="GSC site URL"
)
def step(site_url):
    """Run one evolution step."""
    from engine import evolution

    engine = evolution.SEOEvolutionEngine(site_url)
    df = gsc_client.load_data()
    result = engine.step(df)

    click.echo(f"\nEvolution step complete:")
    click.echo(f"Evaluated: {result['evaluated_count']} interventions")
    click.echo(
        f"Eliminated: {', '.join(result['eliminated_skills']) if result['eliminated_skills'] else 'none'}"
    )
    click.echo(f"Generated: {result.get('new_skill_name', 'none')}")


@evolve.command(name="run")
@click.option(
    "--site-url", default="https://meetspot-irq2.onrender.com/", help="GSC site URL"
)
@click.option("--max-steps", default=15, help="Maximum evolution steps")
@click.option(
    "--min-impressions", default=5, help="Minimum impressions for opportunities"
)
@click.option(
    "--mode",
    default="burst",
    type=click.Choice(["burst", "continuous"]),
    help="burst=back-to-back steps, continuous=smart loop with waits",
)
def run(site_url, max_steps, min_impressions, mode):
    """Run multi-step evolution loop with checkpoint/resume."""
    from engine import evolution

    engine = evolution.SEOEvolutionEngine(site_url)
    engine.run(max_steps=max_steps, min_impressions=min_impressions, mode=mode)


@evolve.command()
@click.option("--days", default=30, help="Days of historical data to use")
@click.option(
    "--site-url", default="https://meetspot-irq2.onrender.com/", help="GSC site URL"
)
def backtest(days, site_url):
    """Run backtest on historical data."""
    from engine import evolution

    result = evolution.backtest(site_url, days=days)

    if "error" in result:
        click.echo(f"Error: {result['error']}")
        return

    click.echo(f"\nBacktest results ({days} days):")
    for skill_name, metrics in result.items():
        click.echo(f"\n{skill_name}:")
        click.echo(f"  Win rate: {metrics['win_rate']:.1%}")
        click.echo(f"  Avg CTR lift: {metrics['avg_ctr_lift']:.2%}")
        click.echo(f"  Coverage: {metrics['coverage']} pages")


if __name__ == "__main__":
    cli()
