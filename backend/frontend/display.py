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
    print_colored("\nSCENARIO:", "yellow")
    print(f"{scenario_info['scenario']} - {scenario_info['description']}")
    
    print_colored("\nCUSTOMER PROFILE:", "yellow")
    profile = scenario_info['customer_profile']
    print(f"Personality: {profile['personality']}")
    print(f"Technical Level: {profile['tech_level']}")
    print(f"Role: {profile['role']}")
    print(f"Industry: {profile['industry']}")
    print(f"Company Size: {profile['company_size']}")
    
    print_colored("\nPRODUCT:", "yellow")
    print(f"{product_info['name']} - {product_info['description']}")
    print("\nKey Features:")
    for feature in product_info['key_features'][:3]:  # Show just 3 features
        print(f"- {feature}")
    
    print_colored("\nCONVERSATION STARTS:", "green")
    print_colored(f"Customer: {scenario_info['initial_query']}", "magenta")
    print() 