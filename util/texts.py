from colorama import Fore, Style

def format_game_info(text: str) -> str:
    return f'{Fore.YELLOW}{text}{Style.RESET_ALL}'

def format_info(text: str) -> str:
    return f'{Fore.WHITE}{text}{Style.RESET_ALL}'

def format_action(text: str) -> str:
    return f'{Fore.GREEN}{text}{Style.RESET_ALL}'

def format_waiting(text: str) -> str:
    return f'{Fore.LIGHTRED_EX}{text}{Style.RESET_ALL}'