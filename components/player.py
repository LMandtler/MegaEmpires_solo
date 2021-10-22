from __future__ import annotations
from typing import List, Tuple, Dict, Set
from components.card import Card
import components.util as util
import random

class Player(object):
    def __init__(self, name: str, ast_ranking: int, handcards: List[Card]) -> None:
        self.name = name
        self.ast_ranking = ast_ranking
        self.ast_position = 0
        self.handcards = handcards
        self.cities: int = 0
        self.priority_threshold = None
        self.trades: Dict[int, int] = {}

    def diff_handcard_value(self, incoming: List[Card]) -> Tuple[int, int]:
        new_handcards = self.handcards + incoming

        current_value = evaluate(self.handcards)
        new_value = evaluate(new_handcards)

        return new_value - current_value

    def calc_offer(self) -> None:
        values = calc_values(self.handcards)
        sorted_handcards = sorted(
            values.items(), key=lambda x: x[1][1], reverse=True)
        value_handcards = evaluate(self.handcards)

        self.priority: Set[Card] = set()
        self.offer: List[Card] = []

        rolling_sum = 0
        for item in filter(lambda x: x[0].tradeable, sorted_handcards):
            self.priority.add(item[0])
            rolling_sum += item[1][0]

            if rolling_sum >= value_handcards * self.priority_threshold:
                break

        self.offer = list(filter(lambda x: x.offerable, self.handcards))

        self.offer.sort(key=lambda x: x.value, reverse=True)

    def evaluate_offer(self, other: Player) -> Tuple[Player, List[Card], List[Card], int]:
        if len(self.handcards) < 3 or len(other.handcards) < 3:
            return None

        gain_options = sorted([
            card for card in other.offer
            if card in self.priority and card not in other.priority
        ], key=lambda x: self.order_cards_internal_value(x), reverse=True)
        give_options = sorted([
            card for card in self.offer
            if card in other.priority and card not in gain_options
        ], key=lambda x: other.order_cards_internal_value(x), reverse=True)

        gain_value = sum([self.get_internal_value(card)
                         for card in gain_options])

        if gain_options and give_options:
            return (other, gain_options, give_options, gain_value)
        elif gain_options:
            return (other, gain_options, None, gain_value*0.5)
        else:
            # TODO: Search for suboptimal trading partner
            #    (meaning I can fulfill my own priority without fulfilling his but giving him Value)
            return None

    def trade(self, trade_option: Tuple[Player, List[Card], List[Card], int]) -> bool:
        (other, gain_options, give_options, intern_value) = trade_option
        # gain and give needs to be filled to 2 cards. gain_value and give_value should be identical at that point
        # then 3 card is added by taking card with lowest value

        # Falls give_options leer ist, kann keine Priorität des Gegenübers erfüllt werden.
        # In diesem Fall sind alle eigenen Karten außer der ersten gain_options möglich.
        if give_options is None:
            give_options = sorted(
                filter(
                    lambda x: x is not gain_options[0] and x.value > 0,
                    self.handcards
                ), key=lambda x: other.order_cards_internal_value(x),
                reverse=True
            )

        # Man hat sich gefunden, indem die Prios übereinstimmen. Jetzt wird der konkrete Handel besprochen.
        # Dafür werden abwechselnd Karten benannt, die abgegeben werden und dem anderen Spieler bestmöglich helfen.
        gain = []
        give = []

        if gain_options[0].value < give_options[0].value:
            # den Handel umdrehen. Das heißt, vom anderen Spieler aus aufrufen.
            # Dann brauche ich die Logik nur einmal und muss nicht viele if/else haben
            return other.trade((self, give_options, gain_options,
                                None))

        # Die Karten werden nach dem Schema A B B A hinzugefügt.
        # Der größere Wert beginnt. Das heißt Self beginnt eine Karte zu bekommen.
        gain.append(gain_options.pop(0))
        other.handcards.remove(gain[0])
        give.append(give_options.pop(0))
        self.handcards.remove(give[0])

        if give_options:
            # give_options hat noch etwas, dann wird das auf jeden Fall gegeben, damit der geringere Wert ausgeglichen wird.
            give.append(give_options.pop(0))
            self.handcards.remove(give[1])
            # Abhängig von der Differenz
            diff = evaluate(give) - evaluate(gain)
            if diff > 0:
                gain.append(other.get_card_by_value(diff, give))
            else:
                gain.append(other.get_lowest_value_card(give, calamity=False))
        else:
            # give_options hat nichts mehr, dann wird gain mit einer niedrigwertigen Karte aufgefüllt.
            gain.append(other.get_lowest_value_card(give, calamity=False))
            if None in gain or None in give:
                self.cleanup_trade(give)
                other.cleanup_trade(gain)
                return False
            diff = evaluate(gain) - evaluate(give)
            # Anschließend versucht give zu matchen
            give.append(self.get_card_by_value(diff, gain))

        if None in gain or None in give:
            self.cleanup_trade(give)
            other.cleanup_trade(gain)
            return False

        return self.fulfill_trade(other, gain, give)

    def fulfill_trade(self, other: Player, gain: List[Card], give: List[Card]) -> bool:
        give.append(self.get_lowest_value_card([]))
        gain.append(other.get_lowest_value_card([]))
        if None in gain or None in give:
            self.cleanup_trade(give)
            other.cleanup_trade(gain)
            return False
        # diff_self = self.diff_handcard_value(gain)
        # diff_other = other.diff_handcard_value(give)
        self.handcards.extend(gain)
        other.handcards.extend(give)
        # print(self, other, gain, give, evaluate(gain), evaluate(give), diff_self, diff_other)
        self.calc_offer()
        other.calc_offer()
        return True

    def cleanup_trade(self, cards: List[Card]) -> None:
        self.handcards += filter(lambda x: x is not None, cards)

    def get_lowest_value_card(self, offered_cards: List[Card], calamity: bool = True) -> Card:
        # order handcards by internal value in desc order
        values = calc_values(
            list(filter(lambda x: x not in offered_cards and x not in self.priority, self.handcards)))
        card = next(
            filter(
                lambda x: x.tradeable if calamity else x.value >= 0,
                [item[0] for item in sorted(
                    values.items(), key=lambda x: (x[1][1], x[0].value), reverse=False)]
            ), None
        )
        if card is None:
            return None

        self.handcards.remove(card)
        return card

    def get_card_by_value(self, value: int, offered_cards: List[Card]) -> Card:
        values = calc_values(
            list(filter(lambda x: x not in offered_cards and x not in self.priority, self.handcards)))
        return_card = None
        for card in filter(lambda x: x.value >= 0, [item[0] for item in sorted(
                values.items(), key=lambda x: x[1][1], reverse=False)]):
            return_card = card
            if card.value >= value:
                break
        if return_card is None:
            return None

        self.handcards.remove(return_card)
        return return_card

    def ascend(self) -> None:
        self.ast_position += 1

    def get_internal_value(self, card: Card) -> int:
        current_value = calc_card_value(card, self.handcards)
        new_value = calc_card_value(card, self.handcards + [card])
        return new_value - current_value

    def reveal_calamities(self) -> List[Card]:
        calamities = list(filter(lambda x: x.is_calamity(), self.handcards))
        for card in calamities:
            self.handcards.remove(card)
        return calamities

    def discard_cards(self, cards: List[Card], trailing_str: str = '') -> None:
        self.print_handcards(trailing_str)
        discards = input(util.format_action(
            f'Please name cards you want to discard in comma-separated fashion. trailing - for whole set:\n')).split(',')
        for discard in discards:
            if discard == '':
                continue
            elif discard[0] == '-':
                # get the whole set within the handcards
                extracted_cards = [
                    card for card in self.handcards if card.name == discard[1:]]
                cards.extend(extracted_cards)
                self.handcards = [
                    card for card in self.handcards if card not in extracted_cards]
            else:
                for card in self.handcards:
                    if card.name == discard:
                        self.handcards.remove(card)
                        cards.append(card)
                        break

    def draw_card(self, other:Player) -> None:
        card = random.choice(other.handcards)
        other.handcards.remove(card)
        self.handcards.append(card)

    def order_cities(self) -> Tuple[int, int]:
        return (self.cities, self.ast_ranking)

    def order_ast_position(self) -> Tuple[int, int]:
        return (self.ast_position, self.ast_ranking)

    def order_cards_internal_value(self, card: Card) -> Tuple[int, int, int, str]:
        return (self.get_internal_value(card), calc_set_value(card, self.handcards), card.value, card.name)

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f'{self.name}'

    def print_handcards(self, trailing_str: str = '', calamities: bool = False) -> None:
        str = ''
        sorted_handcards = sorted(
            list(set(self.handcards)), key=lambda x: (x.value, calc_set_value(x, self.handcards), x.name), reverse=True)
        if not calamities:
            sorted_handcards = filter(lambda x: x.value >= 0, sorted_handcards)
        for card in sorted_handcards:
            count = self.handcards.count(card)
            str += f'{trailing_str}{"*" if count == card.max_count else " "}{card.name:<10}({card.value}): {count}/{card.max_count} cards with a set value of {calc_set_value(card, self.handcards):>3}\n'
        print(util.format_info(str))


def evaluate(cards: List[Card]) -> int:
    value = 0
    for card in filter(lambda x: x.value > 0, set(cards)):
        value = value + calc_set_value(card, cards)

    return value


def calc_card_value(card: Card, cards: List[Card]) -> float:
    count = cards.count(card)
    if count == 0:
        return 0
    value = calc_set_value(card, cards)
    return value / count


def calc_set_value(card: Card, cards: List[Card]) -> int:
    count = cards.count(card)
    return count * count * card.value


def calc_values(cards: List[Card]) -> Dict[Card, Tuple[int, float, int]]:
    values = {}
    for card in set(cards):
        card_count = cards.count(card)
        set_value = calc_set_value(card, cards)
        card_value = calc_card_value(card, cards)

        values[card] = (set_value, card_value, card_count)
    return values
