from typing import List, Dict, Tuple
from components.card import Card
from components.player import Player, evaluate
import components.util as util
import random
import json
import jsonpickle
from pathlib import Path


def print_step() -> None:
    print('____________________________________________________________')


class Game(object):
    def __init__(self, config: Dict, options: Dict) -> None:
        self.stacks = {1: [], 2: [], 3: [], 4: [],
                       5: [], 6: [], 7: [], 8: [], 9: []}

        config = config[options.player][options.map]

        if options.player == "5":
            top_stacks = self.prepare_stacks_from_config(
                config['top'], options)
            bottom_stacks = self.prepare_stacks_from_config(
                config['bottom'], options)

            self.shuffle_stacks_with_configuration(top_stacks, options)
            self.shuffle_stacks(bottom_stacks)

            self.add_cards_to_stacks(top_stacks)
            self.add_cards_to_stacks(bottom_stacks)

        if options.player == "9":
            top_stacks = self.prepare_stacks_from_config(
                config['top'], options)
            middle_stacks = self.prepare_stacks_from_config(
                config['middle'], options)
            bottom_stacks = self.prepare_stacks_from_config(
                config['bottom'], options)

            self.shuffle_stacks(top_stacks)
            self.shuffle_stacks(middle_stacks)
            self.shuffle_stacks(bottom_stacks)

            self.add_cards_to_stacks(top_stacks)
            self.add_cards_to_stacks(middle_stacks)
            self.add_cards_to_stacks(bottom_stacks)

        self.prepare_players_from_config(config['players'])

        self.round = 1
        self.hand_limit = 8
        self.water = Card('water', 0, 0)

        self.discard_pile: List[Card] = []
        self.calamities: Dict[Card, Player] = {}
        self.trailing_str = '  '

        self.dispatch_calamity_resolution = {
            "Banditry": self.resolve_banditry,
            "Corruption": self.resolve_corruption,
        }

    def prepare_stacks_from_config(self, config: Dict, options: Dict) -> Dict[int, List[Card]]:
        stacks = {}
        for item in config:
            cards = [Card(item['name'], item['value'], item['count'], item['calamity'],
                          item['tradeable'], item['offerable'])] * item['count']
            if abs(item['value']) in stacks:
                stacks[abs(item['value'])].extend(cards)
            else:
                stacks[abs(item['value'])] = cards
        return stacks

    def shuffle_stacks_with_configuration(self, stacks: Dict[int, List[Card]], options: Dict) -> None:
        for key, stack in stacks.items():
            commodities = list(filter(lambda x: not x.is_calamity(), stack))
            calamities = list(filter(lambda x: x.is_calamity(), stack))

            # set aside as many cards as there are players
            top_stack = random.sample(commodities, int(options.player))
            random.shuffle(top_stack)
            for card in top_stack:
                commodities.remove(card)

            # shuffle remaining cards and calamities
            bottom_stack = commodities + calamities
            random.shuffle(bottom_stack)

            stacks[key] = top_stack + bottom_stack

    def shuffle_stacks(self, stacks: Dict[int, List[Card]]) -> None:
        for stack in stacks.values():
            random.shuffle(stack)

    def prepare_players_from_config(self, config: Dict) -> None:
        self.players: List[Player] = []
        for item in config:
            self.players.append(Player(item['name'], item['ast_ranking'], []))

    def add_cards_to_stacks(self, stacks: Dict[int, List[Card]]) -> None:
        for stack in stacks.items():
            self.stacks[stack[0]].extend(stack[1])

    def enter_cities(self, cities: int = None) -> None:
        for player in self.players:
            player.cities = int(
                input(util.format_action(f'{player.name}:'))) if cities is None else cities

    def prepare_trading_queue(self) -> None:
        self.trading_queue = sorted(
            self.players, key=lambda x: x.order_ast_position())

        for player in self.players:
            player.priority_threshold = 0.5
            player.calc_offer()

    def perform_trade(self) -> bool:
        actor = self.trading_queue.pop(0)
        max_value: Tuple[Player, List[Card], List[Card], int] = None
        for other_player in self.trading_queue:
            offer = actor.evaluate_offer(other_player)
            if max_value is None and offer is not None:
                max_value = offer
            elif offer is not None and offer[3] > max_value[3]:
                max_value = offer

        self.trading_queue.append(actor)

        if max_value is not None:
            if actor.trade(max_value):
                if self.round in actor.trades:
                    actor.trades[self.round] += 1
                else:
                    actor.trades[self.round] = 1
                return True
            else:
                return False
        else:
            return False

    def discard_excess_calamities(self, calamities: List[Card], threshold: int) -> None:
        while len(calamities) > threshold:
            card = random.choice(calamities)
            calamities.remove(card)
            self.discard_pile.append(card)

    def discard_calamities(self, player: Player, calamities: List[Card]) -> None:
        majors = [x for x in calamities if x.calamity == 'major']
        minors = [x for x in calamities if x.calamity == 'minor']

        self.discard_excess_calamities(majors, 2)
        calamities = majors + minors
        self.discard_excess_calamities(calamities, 3)

        for calamity in calamities:
            self.calamities[calamity] = player

    def resolve_banditry(self, player: Player) -> None:
        print(util.format_info(
            f'You have to discard 2 cards. You can prevent each card by paying 4 treasury token each.'))
        player.print_handcards(self.trailing_str)
        count = 2 - \
            int(input(util.format_action(f'How many cards do you want to prevent?\n')))
        cards = []

        while len(cards) < count:
            print(util.format_info(
                f'You have to discard {count - len(cards)} more cards'))
            player.discard_cards(cards, self.trailing_str)

        self.discard_pile += cards

    def resolve_corruption(self, player: Player) -> None:
        face_value = int(input(util.action(
            f'Please type in actual face value to discard. Base:10, Law:-5, Coinage:+5, Wonder of the World:+5\n')))
        print(util.format_info(
            f'You have to discard cards with a face value of {face_value}'))
        cards = []

        discard_value = 0

        while discard_value < face_value:
            print(util.info(
                f'You have to discard {face_value - discard_value} additional face value'))
            player.discard_cards(cards, self.trailing_str)
            discard_value = sum([card.value for card in cards])

        self.discard_pile += cards

    def game_loop(self) -> None:
        print(util.format_game_info(
            f'\nGAME_INFO: Round {self.round} starts: '))
        print_step()
        self.phase_1_tax_collection()
        self.phase_2_population_expansion()
        self.phase_3_movement()
        self.phase_4_conflict()
        self.phase_5_city_construction()
        self.phase_6_trade_card_acquisition()
        self.phase_7_trade()
        self.phase_8_calamity_selection()
        self.phase_9_calamity_resolution()
        self.phase_10_special_abilities()
        self.phase_11_remove_surplus_populations()
        self.phase_12_civilization_advances_acquisition()
        self.phase_13_ast_alteration()
        self.next_round()
        print_step()
        self.save_game()

    def phase_1_tax_collection(self) -> None:
        print(util.format_game_info(f'GAME_INFO: tax collection'))
        input(util.format_action(f'Please collect the taxes'))
        input(util.format_action(f'Are there any tax revolts?'))

    def phase_2_population_expansion(self) -> None:
        print(util.format_game_info(f'GAME_INFO: population expansion'))
        input(util.format_action(f'Please expand the populations'))
        input(util.format_action(f'Please do the census'))

    def phase_3_movement(self) -> None:
        print(util.format_game_info(f'GAME_INFO: movement'))
        input(util.format_action(f'Please move in census order'))

    def phase_4_conflict(self) -> None:
        print(util.format_game_info(f'GAME_INFO: conflict'))
        input(util.format_action(f'Resolution of token conflicts'))

        print(util.format_info(f'Resolution of city attacks'))
        while input(util.format_action(f'Was a city destroyed?')) == 'y':
            attacker_name, defender_name = input(util.format_action(
                f'Please name attacker and defender separated by a comma:\n')).split(',')

            for player in self.players:
                if player.name == attacker_name:
                    attacker = player
                if player.name == defender_name:
                    defender = player
            attacker.draw_card(defender)

    def phase_5_city_construction(self) -> None:
        print(util.format_game_info(f'GAME_INFO: city construction'))
        input(util.format_action(f'Construct cities'))
        input(util.format_action(f'Surplus population removal'))

    def phase_6_trade_card_acquisition(self) -> None:
        print(util.format_game_info(f'GAME_INFO: Trade card acquisition'))
        print(util.format_info(f'Please enter number of cities for each nation'))
        self.enter_cities()
        for player in sorted(self.players, key=lambda x: x.order_cities()):
            for city in range(player.cities):
                city = city + 1

                card = self.stacks[city].pop(
                    0) if self.stacks[city] else self.water
                player.handcards.append(card)

    def phase_7_trade(self, trades: int = 1000) -> None:
        print(util.format_game_info(f'GAME_INFO: resolving trades'))
        self.prepare_trading_queue()
        counter = 0
        for _ in range(trades):
            val = self.perform_trade()
            if not val:

                counter += 1
            else:
                counter = 0

    def phase_8_calamity_selection(self) -> None:
        print(util.format_game_info(f'GAME_INFO: resolving calamity selection'))
        for player in self.players:
            calamities = player.reveal_calamities()
            self.discard_calamities(player, calamities)

    def phase_9_calamity_resolution(self) -> None:
        print(util.format_game_info(f'GAME_INFO: resolving calamity resolution'))
        for calamity in sorted(self.calamities, key=lambda x: x.order_calamity(), reverse=True):
            player = self.calamities.pop(calamity)
            input(util.format_action(
                f'{self.trailing_str}{player.name} resolve {calamity.name}'))
            if calamity.name in self.dispatch_calamity_resolution:
                self.dispatch_calamity_resolution[calamity.name](player)
            self.discard_pile.append(calamity)

    def phase_10_special_abilities(self) -> None:
        print(util.format_game_info(f'GAME_INFO: special abilities'))
        input(util.format_action(f'Resolve special abilities'))

    def phase_11_remove_surplus_populations(self) -> None:
        print(util.format_game_info(f'GAME_INFO: remove surplus populations'))
        input(util.format_action(f'Remove surplus populations'))

    def phase_12_civilization_advances_acquisition(self) -> None:
        print(util.format_game_info(
            f'GAME_INFO: resolving civilization_advances_acquisition'))
        for player in self.players:
            if len(player.handcards) == 0:
                continue
            print_step()
            print(util.format_info(
                f'\n{self.trailing_str}{player.name} has {len(player.handcards)} cards:'))

            cards = []

            player.discard_cards(cards, self.trailing_str*2)

            while len(player.handcards) > self.hand_limit:
                print(util.format_info(
                    f'{self.trailing_str}Please discard at least {len(player.handcards) - self.hand_limit} more cards.'))
                player.discard_cards(cards)

            while input(util.format_action(f'Are you finished with discarding cards? [{"n"} to decline]:')) == 'n':
                player.discard_cards(cards)

            input(util.format_action(
                f'{self.trailing_str}You handed in {len(cards)} with a value of {evaluate(cards)}'))
            self.discard_pile += cards

    def phase_13_ast_alteration(self) -> None:
        print(util.format_game_info(f'GAME_INFO: ast_alteration'))
        input(util.format_action(f'Move succession markers'))
        input(util.format_action(f'Check for game end'))
        print(util.format_info(f'Reshuffling trade cards'))
        stacks = {}
        for card in self.discard_pile:
            self.discard_pile.remove(card)
            if abs(card.value) in stacks:
                stacks[abs(card.value)].append(card)
            else:
                stacks[abs(card.value)] = [card]

        for stack in stacks.values():
            random.shuffle(stack)

        self.add_cards_to_stacks(stacks)

    def next_round(self) -> None:
        self.round = self.round + 1

    def save_game(self) -> None:
        jsonStr = json.dumps(jsonpickle.encode(self, keys=True))
        file = Path(f'temp/autosave_round_{self.round}.json')
        file.parent.mkdir(parents=True, exist_ok=True)
        file.touch(exist_ok=True)
        file.write_text(jsonStr)

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f'{self.players}'
