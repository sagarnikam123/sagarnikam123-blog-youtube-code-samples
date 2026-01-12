#!/usr/bin/env python3
"""
Command-Line Interface for the Prometheus Testing Framework.

This module provides the main CLI entry point for running tests, generating reports,
and cleaning up resources. It supports various options for deployment mode, k6 configuration,
and test execution.

Requirements: 10.2, 10.4, 10.8

Usage:
    # Run all tests
    python3 -m tests.cli run --platform minikube --config config/default.yaml

    # Run specific test type
    python3 -m tests.cli run --type sanity --platform docker

    # Run load tests with k6 options
    python3 -m tests.cli run --type load --platform eks --k6-vus 100 --k6-duration 30m

    # Generate report from results
    python3 -m tests.cli report --format html --output results/

    # Clean up test resources
    python3 -m tests.cli cleanup --platform minikube
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table

# Set up logging with rich handler
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True, show_time=False)],
)
logger = logging.getLogger(__name__)
console = Console()


# Valid options for CLI arguments
VALID_PLATFORMS = ["minikube", "eks", "gke", "aks", "docker", "binary"]
VALID_DEPLOYMENT_MODES = ["monolithic", "distributed"]
VALID_TEST_TYPES = [
    "sanity", "integration", "load", "stress", "performance",
    "scalability", "endurance", "reliability", "chaos", "regression", "security"
]
VALID_REPORT_FORMATS = ["json", "markdown", "html", "csv"]


class CLIContext:
    """Context object for CLI commands."""

    def __init__(self):
        self.verbose = False
        self.config_path: Optional[Path] = None
        self.platform: Optional[str] = None
        self.deployment_mode: Optional[str] = None


pass_context = click.make_pass_decorator(CLIContext, ensure=True)


def validate_platform(ctx, param, value):
    """Validate platform option."""
    if value and value not in VALID_PLATFORMS:
        raise click.BadParameter(
            f"Invalid platform '{value}'. Must be one of: {', '.join(VALID_PLATFORMS)}"
        )
    return value


def validate_deployment_mode(ctx, param, value):
    """Validate deployment mode option."""
    if value and value not in VALID_DEPLOYMENT_MODES:
        raise click.BadParameter(
            f"Invalid deployment mode '{value}'. Must be one of: {', '.join(VALID_DEPLOYMENT_MODES)}"
        )
    return value


def validate_test_type(ctx, param, value):
    """Validate test type option."""
    if value:
        for t in value:
            if t not in VALID_TEST_TYPES:
                raise click.BadParameter(
                    f"Invalid test type '{t}'. Must be one of: {', '.join(VALID_TEST_TYPES)}"
                )
    return value


def validate_report_format(ctx, param, value):
    """Validate report format option."""
    if value:
        for f in value:
            if f not in VALID_REPORT_FORMATS:
                raise click.BadParameter(
                    f"Invalid format '{f}'. Must be one of: {', '.join(VALID_REPORT_FORMATS)}"
                )
    return value


@click.group()
@click.option(
    "-v", "--verbose",
    is_flag=True,
    help="Enable verbose output"
)
@click.option(
    "-c", "--config",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file"
)
@click.version_option(version="0.1.0", prog_name="prometheus-test")
@pass_context
def cli(ctx: CLIContext, verbose: bool, config: Optional[Path]):
    """
    Prometheus Installation and Testing Framework CLI.

    Run tests, generate reports, and manage test resources for Prometheus deployments.

    Requirements: 10.2, 10.4, 10.8
    """
    ctx.verbose = verbose
    ctx.config_path = config

    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled")



@cli.command()
@click.option(
    "--platform", "-p",
    type=click.Choice(VALID_PLATFORMS, case_sensitive=False),
    default="minikube",
    help="Target platform for testing"
)
@click.option(
    "--deployment-mode", "-m",
    type=click.Choice(VALID_DEPLOYMENT_MODES, case_sensitive=False),
    default="monolithic",
    help="Deployment mode (monolithic or distributed)"
)
@click.option(
    "--type", "-t", "test_types",
    multiple=True,
    type=click.Choice(VALID_TEST_TYPES, case_sensitive=False),
    help="Test type(s) to run (can be specified multiple times)"
)
@click.option(
    "--prometheus-url",
    type=str,
    help="Prometheus URL to test (overrides config)"
)
@click.option(
    "--k6-vus",
    type=int,
    default=None,
    help="Number of k6 virtual users for load tests"
)
@click.option(
    "--k6-duration",
    type=str,
    default=None,
    help="Duration for k6 load tests (e.g., 30m, 1h)"
)
@click.option(
    "--parallel/--sequential",
    default=False,
    help="Run tests in parallel or sequential mode"
)
@click.option(
    "--timeout",
    type=int,
    default=300,
    help="Default timeout for tests in seconds"
)
@click.option(
    "--fail-fast",
    is_flag=True,
    help="Stop on first test failure"
)
@click.option(
    "--output", "-o",
    type=click.Path(path_type=Path),
    default=Path("./results"),
    help="Output directory for test results"
)
@pass_context
def run(
    ctx: CLIContext,
    platform: str,
    deployment_mode: str,
    test_types: tuple,
    prometheus_url: Optional[str],
    k6_vus: Optional[int],
    k6_duration: Optional[str],
    parallel: bool,
    timeout: int,
    fail_fast: bool,
    output: Path,
):
    """
    Run Prometheus tests.

    Execute tests against a Prometheus deployment. Supports running all tests,
    specific test types, or individual tests.

    Requirements: 10.2, 10.3, 10.4, 10.8

    Examples:

        # Run all tests on minikube
        python3 -m tests.cli run --platform minikube

        # Run sanity tests on docker
        python3 -m tests.cli run --type sanity --platform docker

        # Run load tests with k6 options
        python3 -m tests.cli run --type load --k6-vus 100 --k6-duration 30m

        # Run distributed tests on EKS
        python3 -m tests.cli run --platform eks --deployment-mode distributed
    """
    try:
        # Import framework modules
        from .framework.config import load_config, TestConfig
        from .framework.runner import TestRunner, RunnerConfig, ExecutionMode, TestType
        from .framework.reporter import ReportGenerator

        console.print(f"\n[bold blue]Prometheus Test Framework[/bold blue]")
        console.print(f"Platform: [cyan]{platform}[/cyan]")
        console.print(f"Deployment Mode: [cyan]{deployment_mode}[/cyan]")

        # Validate deployment mode compatibility with platform
        if platform in ["docker", "binary"] and deployment_mode == "distributed":
            console.print(
                f"[bold red]Error:[/bold red] Platform '{platform}' only supports monolithic deployment mode",
                style="red"
            )
            sys.exit(1)

        # Load configuration
        config_path = ctx.config_path
        if config_path:
            console.print(f"Config: [cyan]{config_path}[/cyan]")

        config = load_config(
            config_path=config_path,
            platform=platform,
            deployment_mode=deployment_mode,
            prometheus_url=prometheus_url,
            k6_vus=k6_vus,
            k6_duration=k6_duration,
        )

        # Create runner configuration
        runner_config = RunnerConfig(
            execution_mode=ExecutionMode.PARALLEL if parallel else ExecutionMode.SEQUENTIAL,
            default_timeout_seconds=timeout,
            fail_fast=fail_fast,
            prometheus_url=prometheus_url or config.prometheus.url,
        )

        # Create test runner
        runner = TestRunner(config=config, runner_config=runner_config)

        # Determine which tests to run
        if test_types:
            console.print(f"Test Types: [cyan]{', '.join(test_types)}[/cyan]")
            types_to_run = [TestType(t) for t in test_types]
            suite_result = runner.run_suite(types_to_run)
        else:
            console.print("Running: [cyan]All enabled tests[/cyan]")
            suite_result = runner.run_all()

        # Generate and save report
        output.mkdir(parents=True, exist_ok=True)
        reporter = ReportGenerator(output_dir=output)
        report = reporter.create_report(
            suite_result=suite_result,
            deployment_mode=deployment_mode,
        )
        saved_files = reporter.save_report(report)

        # Display results summary
        _display_results_summary(suite_result, report, saved_files)

        # Return proper exit code
        exit_code = runner.get_exit_code()
        sys.exit(exit_code)

    except ImportError as e:
        console.print(f"[bold red]Import Error:[/bold red] {e}", style="red")
        console.print("Make sure all dependencies are installed: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}", style="red")
        if ctx.verbose:
            console.print_exception()
        sys.exit(1)


def _display_results_summary(suite_result, report, saved_files):
    """Display test results summary in a formatted table."""
    console.print("\n")

    # Create summary table
    table = Table(title="Test Results Summary", show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")

    status_style = "green" if report.overall_status == "passed" else "red"
    table.add_row("Status", f"[{status_style}]{report.overall_status.upper()}[/{status_style}]")
    table.add_row("Total Tests", str(report.total_tests))
    table.add_row("Passed", f"[green]{report.passed_tests}[/green]")
    table.add_row("Failed", f"[red]{report.failed_tests}[/red]")
    table.add_row("Skipped", str(report.skipped_tests))
    table.add_row("Success Rate", f"{report.success_rate:.1f}%")
    table.add_row("Duration", f"{report.duration_seconds:.2f}s")

    console.print(table)

    # Show saved files
    if saved_files:
        console.print("\n[bold]Reports saved to:[/bold]")
        for f in saved_files:
            console.print(f"  • {f}")



@cli.command()
@click.option(
    "--format", "-f", "formats",
    multiple=True,
    type=click.Choice(VALID_REPORT_FORMATS, case_sensitive=False),
    default=["json", "markdown", "html"],
    help="Report format(s) to generate"
)
@click.option(
    "--input", "-i",
    type=click.Path(exists=True, path_type=Path),
    help="Input JSON report file to convert"
)
@click.option(
    "--output", "-o",
    type=click.Path(path_type=Path),
    default=Path("./results"),
    help="Output directory for reports"
)
@click.option(
    "--name",
    type=str,
    default=None,
    help="Base name for output files"
)
@pass_context
def report(
    ctx: CLIContext,
    formats: tuple,
    input: Optional[Path],
    output: Path,
    name: Optional[str],
):
    """
    Generate test reports.

    Convert existing JSON reports to other formats or generate new reports
    from test results.

    Requirements: 11.3, 11.4, 11.5

    Examples:

        # Generate HTML report from JSON
        python3 -m tests.cli report --input results/test_report.json --format html

        # Generate multiple formats
        python3 -m tests.cli report --input results/test_report.json -f html -f markdown -f csv

        # Specify output directory
        python3 -m tests.cli report --input results/test_report.json --output ./reports
    """
    try:
        from .framework.reporter import ReportGenerator, FullTestReport

        console.print(f"\n[bold blue]Report Generator[/bold blue]")

        if not input:
            console.print("[bold red]Error:[/bold red] --input is required for report generation")
            console.print("Provide a JSON report file to convert to other formats.")
            sys.exit(1)

        console.print(f"Input: [cyan]{input}[/cyan]")
        console.print(f"Formats: [cyan]{', '.join(formats)}[/cyan]")
        console.print(f"Output: [cyan]{output}[/cyan]")

        # Load existing report
        reporter = ReportGenerator(output_dir=output)
        report_data = reporter.load_report(input)

        # Save in requested formats
        saved_files = reporter.save_report(
            report=report_data,
            formats=list(formats),
            base_name=name,
        )

        console.print("\n[bold green]Reports generated successfully![/bold green]")
        for f in saved_files:
            console.print(f"  • {f}")

        sys.exit(0)

    except FileNotFoundError as e:
        console.print(f"[bold red]Error:[/bold red] File not found: {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}", style="red")
        if ctx.verbose:
            console.print_exception()
        sys.exit(1)


@cli.command()
@click.option(
    "--platform", "-p",
    type=click.Choice(VALID_PLATFORMS, case_sensitive=False),
    required=True,
    help="Platform to clean up"
)
@click.option(
    "--namespace",
    type=str,
    default="monitoring",
    help="Kubernetes namespace (for k8s platforms)"
)
@click.option(
    "--force",
    is_flag=True,
    help="Force cleanup without confirmation"
)
@click.option(
    "--all",
    "cleanup_all",
    is_flag=True,
    help="Clean up all resources including data volumes"
)
@pass_context
def cleanup(
    ctx: CLIContext,
    platform: str,
    namespace: str,
    force: bool,
    cleanup_all: bool,
):
    """
    Clean up test resources.

    Remove Prometheus deployments, containers, pods, and volumes created during testing.

    Requirements: 10.6

    Examples:

        # Clean up minikube deployment
        python3 -m tests.cli cleanup --platform minikube

        # Clean up docker containers
        python3 -m tests.cli cleanup --platform docker

        # Force cleanup without confirmation
        python3 -m tests.cli cleanup --platform eks --force

        # Clean up all resources including volumes
        python3 -m tests.cli cleanup --platform minikube --all
    """
    try:
        from .framework.deployer import get_deployer

        console.print(f"\n[bold blue]Resource Cleanup[/bold blue]")
        console.print(f"Platform: [cyan]{platform}[/cyan]")

        if not force:
            if not click.confirm(f"Are you sure you want to clean up {platform} resources?"):
                console.print("Cleanup cancelled.")
                sys.exit(0)

        # Get appropriate deployer
        deployer = get_deployer(platform, namespace=namespace)

        console.print("Cleaning up resources...")

        # Perform teardown
        success = deployer.teardown()

        if success:
            console.print("[bold green]Cleanup completed successfully![/bold green]")
            sys.exit(0)
        else:
            console.print("[bold yellow]Cleanup completed with warnings.[/bold yellow]")
            sys.exit(0)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}", style="red")
        if ctx.verbose:
            console.print_exception()
        sys.exit(1)


@cli.command()
@pass_context
def info(ctx: CLIContext):
    """
    Display framework information.

    Show version, available platforms, test types, and system information.
    """
    try:
        from .framework.reporter import ReportGenerator

        console.print(f"\n[bold blue]Prometheus Test Framework[/bold blue]")
        console.print(f"Version: [cyan]0.1.0[/cyan]")

        # Get test runner host info
        host_info = ReportGenerator.get_test_runner_host_info()

        # System info table
        table = Table(title="System Information", show_header=True, header_style="bold magenta")
        table.add_column("Property", style="cyan")
        table.add_column("Value")

        table.add_row("OS", f"{host_info.os_name} {host_info.os_version}")
        table.add_row("Python Version", host_info.python_version)
        table.add_row("Hostname", host_info.hostname)
        table.add_row("k6 Version", host_info.k6_version or "Not installed")
        table.add_row("kubectl Version", host_info.kubectl_version or "Not installed")

        console.print(table)

        # Available platforms
        console.print("\n[bold]Available Platforms:[/bold]")
        for p in VALID_PLATFORMS:
            console.print(f"  • {p}")

        # Available test types
        console.print("\n[bold]Available Test Types:[/bold]")
        for t in VALID_TEST_TYPES:
            console.print(f"  • {t}")

        # Available report formats
        console.print("\n[bold]Available Report Formats:[/bold]")
        for f in VALID_REPORT_FORMATS:
            console.print(f"  • {f}")

        sys.exit(0)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}", style="red")
        if ctx.verbose:
            console.print_exception()
        sys.exit(1)


@cli.command()
@click.option(
    "--platform", "-p",
    type=click.Choice(VALID_PLATFORMS, case_sensitive=False),
    default="minikube",
    help="Target platform"
)
@click.option(
    "--deployment-mode", "-m",
    type=click.Choice(VALID_DEPLOYMENT_MODES, case_sensitive=False),
    default="monolithic",
    help="Deployment mode"
)
@click.option(
    "--prometheus-url",
    type=str,
    help="Prometheus URL to check"
)
@pass_context
def status(
    ctx: CLIContext,
    platform: str,
    deployment_mode: str,
    prometheus_url: Optional[str],
):
    """
    Check Prometheus deployment status.

    Verify that Prometheus is running and accessible on the target platform.

    Examples:

        # Check minikube deployment
        python3 -m tests.cli status --platform minikube

        # Check specific URL
        python3 -m tests.cli status --prometheus-url http://localhost:9090
    """
    try:
        from .framework.prometheus_api import PrometheusAPIClient

        console.print(f"\n[bold blue]Prometheus Status Check[/bold blue]")
        console.print(f"Platform: [cyan]{platform}[/cyan]")
        console.print(f"Deployment Mode: [cyan]{deployment_mode}[/cyan]")

        # Determine URL
        url = prometheus_url or "http://localhost:9090"
        console.print(f"URL: [cyan]{url}[/cyan]")

        # Create API client and check health
        client = PrometheusAPIClient(base_url=url)

        console.print("\nChecking endpoints...")

        # Check health
        try:
            is_healthy = client.healthcheck()
            health_status = "[green]✓ Healthy[/green]" if is_healthy else "[red]✗ Unhealthy[/red]"
        except Exception as e:
            health_status = f"[red]✗ Error: {e}[/red]"
        console.print(f"  /-/healthy: {health_status}")

        # Check readiness
        try:
            is_ready = client.readiness()
            ready_status = "[green]✓ Ready[/green]" if is_ready else "[red]✗ Not Ready[/red]"
        except Exception as e:
            ready_status = f"[red]✗ Error: {e}[/red]"
        console.print(f"  /-/ready: {ready_status}")

        # Get runtime info
        try:
            runtime_info = client.get_runtime_info()
            console.print(f"\n[bold]Runtime Information:[/bold]")
            if runtime_info:
                console.print(f"  Version: {runtime_info.get('version', 'Unknown')}")
                console.print(f"  Storage Retention: {runtime_info.get('storageRetention', 'Unknown')}")
        except Exception:
            pass

        sys.exit(0)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}", style="red")
        if ctx.verbose:
            console.print_exception()
        sys.exit(1)


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
