"""
Logging module using Rich for beautiful and informative CLI feedback.
"""

import sys
from datetime import datetime

try:
    from rich.console import Console
    from rich.theme import Theme

    custom_theme = Theme({
        "info": "cyan",
        "warning": "yellow",
        "error": "bold red",
        "success": "bold green",
        "highlight": "magenta",
        "dim": "grey50",
    })
    console = Console(theme=custom_theme)
except ImportError:
    console = None


def _format_time() -> str:
    return datetime.now().strftime("%H:%M:%S")


def log_info(msg: str):
    time_str = f"[{_format_time()}]"
    if console:
        console.print(f"[dim]{time_str}[/dim] [cyan]INFO[/cyan]     {msg}")
    else:
        print(f"{time_str} [INFO] {msg}")


def log_success(msg: str):
    time_str = f"[{_format_time()}]"
    if console:
        console.print(f"[dim]{time_str}[/dim] [bold green]SUCCESS[/bold green]  {msg}")
    else:
        print(f"{time_str} [SUCCESS] {msg}")


def log_warn(msg: str):
    time_str = f"[{_format_time()}]"
    if console:
        console.print(f"[dim]{time_str}[/dim] [yellow]WARNING[/yellow]  {msg}")
    else:
        print(f"{time_str} [WARNING] {msg}")


def log_error(msg: str):
    time_str = f"[{_format_time()}]"
    if console:
        console.print(f"[dim]{time_str}[/dim] [bold red]ERROR[/bold red]    {msg}")
    else:
        print(f"{time_str} [ERROR] {msg}")


def log_header(title: str):
    if console:
        console.rule(f"[bold magenta]{title}[/bold magenta]")
    else:
        print(f"\n=== {title} ===\n")
