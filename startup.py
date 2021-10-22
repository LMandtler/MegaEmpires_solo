from game.card import Card
from game.game import Game
from typing import Tuple, Dict
import argparse
import json


def parse_args() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Automize trading in Mega Empires')
    parser.add_argument(
        '-p', '--player', help='number of players', type=str, default='9')
    parser.add_argument(
        '-m', '--map', help='east or west map', type=str, default='west')

    return parser

def print_evaluation(game):
    print('_________EVALUATION________')
    cards: Dict[Card, Tuple[str, int]] = {}
    for player in game.players:
        for card in filter(lambda x: x.value > 0, set(player.handcards)):
            if card not in cards:
                cards[card] = [(player.name, player.handcards.count(card))]
            else:
                cards[card].append((player.name, player.handcards.count(card)))

    for item in sorted(cards.items(), key=lambda x: (x[0].value, x[0].name), reverse=True):
        print(f'{item[0]}: {item[1]}')
    print('_________EVALUATION_END____')
    
def main():
    parser = parse_args()
    options = parser.parse_args()

    with open('config.conf') as config:
        config = json.load(config)[options.player][options.map]

    game = Game(config)
    while True:
        game.game_loop()

if __name__ == '__main__':
    main()
