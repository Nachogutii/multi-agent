from typing import Dict

def print_colored(text: str, color: str = None) -> None:
    """Print text with ANSI color codes."""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "reset": "\033[0m"
    }
    
    if color and color in colors:
        print(f"{colors[color]}{text}{colors['reset']}")
    else:
        print(text)

def print_banner(text: str) -> None:
    """Print a banner with the given text."""
    border = "=" * (len(text) + 4)
    print_colored(border, "cyan")
    print_colored(f"| {text} |", "cyan")
    print_colored(border, "cyan")

def print_scenario_info(scenario_info: Dict, product_info: Dict) -> None:
    """Print information about the current scenario."""
    print_banner("PLG CUSTOMER SERVICE ROLEPLAY")
    print() 