import util.texts as util
from collections.abc import Callable
from typing import Tuple, List
from components.player import Player


def get_input(request: str) -> str:
    return input(util.format_action(request))


def wait_for_action(text: str) -> None:
    input(util.format_action(text))


def get_digit(request: str) -> int:
    user_input = get_input(request)
    if user_input == '':
        return 0
    while not user_input.isdigit():
        user_input = get_input(request)
        if user_input == '':
            return 0
    return int(user_input)


def get_confirmation(request: str) -> bool:
    user_input = get_input(request)
    if user_input == '':
        return False
    while user_input != 'y':
        user_input = get_input(request)
        if user_input == '':
            return False

    return True


def get_player(request: str, valid_players: List[Player]) -> Player:
    user_input = get_input(request)
    if user_input == '':
        return None
    while user_input not in [player.name for player in valid_players]:
        user_input = get_input(request)
        if user_input == '':
            return None

    for player in valid_players:
        if player.name == user_input:
            return player


def get_players(request: str, valid_players: List[Player]) -> Tuple[Player, Player]:
    user_input = get_input(request)
    if user_input == '':
        return None, None
    inputs = user_input.split(',')
    while len(inputs) != 2 or not all(item in [player.name for player in valid_players] for item in inputs):
        user_input = get_input(request)
        if user_input == '':
            return None, None
        inputs = user_input.split(',')

    for player in valid_players:
        if player.name == inputs[0]:
            attacker = player
        if player.name == inputs[1]:
            defender = player

    return attacker, defender
