import components.game
import components.card
import components.player

from typing import Tuple, Dict
import argparse
import json
from pathlib import Path
import jsonpickle


def parse_args() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Automize trading in Mega Empires')
    parser.add_argument(
        '-p', '--player', help='number of players', type=str, default='9')
    parser.add_argument(
        '-m', '--map', help='east or west map', type=str, default='west')
    parser.add_argument(
        '-l', '--load', help='provide the path to a save file to continue a game', type=str)

    return parser

# def print_evaluation(game):
#     print('_________EVALUATION________')
#     cards: Dict[components.game.Card, Tuple[str, int]] = {}
#     for player in game.players:
#         for card in filter(lambda x: x.value > 0, set(player.handcards)):
#             if card not in cards:
#                 cards[card] = [(player.name, player.handcards.count(card))]
#             else:
#                 cards[card].append((player.name, player.handcards.count(card)))

#     for item in sorted(cards.items(), key=lambda x: (x[0].value, x[0].name), reverse=True):
#         print(f'{item[0]}: {item[1]}')
#     print('_________EVALUATION_END____')

def load_game(savefile: Path) -> components.game.Game:
    with savefile.open() as file:
        jsonStr = json.load(file)
    game = jsonpickle.decode(jsonStr, classes=(components.game.Game, components.player.Player, components.card.Card), keys=True)

    return game

def main():
    parser = parse_args()
    options = parser.parse_args()

    if options.load:
        savefile = Path(options.load)
        if savefile.exists():
            game = load_game(savefile)
        else:
            print(f'Please provide a correct path to a save file.\nClosing.')
    else:
        with open('config.conf') as config:
            config = json.load(config)[options.player][options.map]
        game = components.game.Game(config)
    
    while True:
        game.game_loop()

if __name__ == '__main__':
    main()
