from __future__ import annotations
import random
from typing import List, Tuple, Dict, Set
from components.card import Card
import util.texts as util


class Player():
    def __init__(self, name: str, ast_ranking: int, handcards: List[Card]) -> None:
        self.name = name
        self.ast_ranking = ast_ranking
        self.ast_position = 0
        self.handcards = handcards
        self.cities: int = 0
        self.priority_threshold = None
        self.trades: Dict[int, int] = {}
        self.priority: Set[Card] = set()
        self.offer: List[Card] = []

    def diff_handcard_value(self, incoming: List[Card]) -> Tuple[int, int]:
        new_handcards = self.handcards + incoming

        current_value = evaluate(self.handcards)
        new_value = evaluate(new_handcards)

        return new_value - current_value

    def calc_offer(self) -> None:
        # remove full sets from handcards first, so that the player will definitely hold that set.
        # determine full sets first:
        cards = without_full_sets(self.handcards)

        values = calc_values(cards)
        sorted_handcards = sorted(
            values.items(), key=lambda x: x[1][1], reverse=True)
        value_cards = evaluate(cards)

        self.priority = set()
        self.offer = []

        rolling_sum = 0
        for item in filter(lambda x: x[0].tradeable, sorted_handcards):
            self.priority.add(item[0])
            rolling_sum += item[1][0]

            if rolling_sum >= value_cards * self.priority_threshold:
                break

        self.offer = list(filter(lambda x: x.offerable, cards))

        self.offer.sort(key=lambda x: x.value, reverse=True)

    def evaluate_offer(self, other: Player) -> Tuple[Player, List[Card], List[Card], int]:
        if len(without_full_sets(self.handcards)) < 3 or len(without_full_sets(other.handcards)) < 3:
            return None

        gain_options = sorted([
            card for card in other.offer
            if card in self.priority and card not in other.priority
        ], key=self.order_cards_internal_value, reverse=True)
        give_options = sorted([
            card for card in self.offer
            if card in other.priority and card not in gain_options
        ], key=other.order_cards_internal_value, reverse=True)

        gain_value = sum([calc_card_value(card, self.handcards)
                         for card in gain_options])

        if gain_options and give_options:
            return (other, gain_options, give_options, gain_value)
        if gain_options:
            return (other, gain_options, None, gain_value*0.5)
        return None

    def trade(self, trade_option: Tuple[Player, List[Card], List[Card], int]) -> bool:
        (other, gain_options, give_options, _) = trade_option
        # gain and give needs to be filled to 2 cards. gain_value and give_value should be identical at that point
        # then 3 card is added by taking card with lowest value

        # Falls give_options leer ist, kann keine Priorit??t des Gegen??bers erf??llt werden.
        # In diesem Fall sind alle eigenen Karten au??er der ersten gain_options m??glich.
        if give_options is None:
            give_options = sorted(
                filter(
                    lambda x: x is not gain_options[0] and x.value > 0,
                    self.handcards
                ), key=other.order_cards_internal_value,
                reverse=True
            )

        # Man hat sich gefunden, indem die Prios ??bereinstimmen. Jetzt wird der konkrete Handel besprochen.
        # Daf??r werden abwechselnd Karten benannt, die abgegeben werden und dem anderen Spieler bestm??glich helfen.
        gain = []
        give = []

        if gain_options[0].value < give_options[0].value:
            # den Handel umdrehen. Das hei??t, vom anderen Spieler aus aufrufen.
            # Dann brauche ich die Logik nur einmal und muss nicht viele if/else haben
            return other.trade((self, give_options, gain_options,
                                None))

        # Die Karten werden nach dem Schema A B B A hinzugef??gt.
        # Der gr????ere Wert beginnt. Das hei??t Self beginnt eine Karte zu bekommen.
        gain.append(gain_options.pop(0))
        other.handcards.remove(gain[0])
        give.append(give_options.pop(0))
        self.handcards.remove(give[0])

        if give_options:
            # give_options hat noch etwas, dann wird das auf jeden Fall gegeben, damit der geringere Wert ausgeglichen wird.
            give.append(give_options.pop(0))
            self.handcards.remove(give[1])
            # Abh??ngig von der Differenz
            diff = evaluate(give) - evaluate(gain)
            if diff > 0:
                gain.append(other.get_card_by_value(diff, give))
            else:
                gain.append(other.get_lowest_value_card(give, calamity=False))
        else:
            # give_options hat nichts mehr, dann wird gain mit einer niedrigwertigen Karte aufgef??llt.
            gain.append(other.get_lowest_value_card(give, calamity=False))
            if None in gain or None in give:
                self.cleanup_trade(give)
                other.cleanup_trade(gain)
                return False
            diff = evaluate(gain) - evaluate(give)
            # Anschlie??end versucht give zu matchen
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

        self.track_last_owner(give)
        other.track_last_owner(gain)
        # print(self, other, gain, give, evaluate(gain), evaluate(give), diff_self, diff_other)
        self.calc_offer()
        other.calc_offer()
        return True

    def cleanup_trade(self, cards: List[Card]) -> None:
        self.handcards += filter(lambda x: x is not None, cards)

    def track_last_owner(self, cards: List[Card]) -> None:
        for card in filter(lambda x: x.is_calamity(), cards):
            card.last_owner = self

    def get_lowest_value_card(self, offered_cards: List[Card], calamity: bool = True) -> Card:
        # order handcards by internal value in desc order
        cards = without_full_sets(self.handcards)
        values = calc_values(
            list(filter(lambda x: x not in offered_cards and x not in self.priority, cards)))
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
        cards = without_full_sets(self.handcards)
        values = calc_values(
            list(filter(lambda x: x not in offered_cards and x not in self.priority, cards)))
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

    def reveal_calamities(self) -> List[Card]:
        calamities = list(filter(lambda x: x.is_calamity(), self.handcards))
        for card in calamities:
            self.handcards.remove(card)
        return calamities

    def discard_cards(self, cards: List[Card], preceding_str: str = '') -> None:
        self.print_handcards(preceding_str)
        discards = input(util.format_action(
            'Please name cards you want to discard in comma-separated fashion.\n'
            'preceding * to discard whole set:\n'
            'preceding - to add cards back to handcards\n'
        )).split(',')
        for discard in discards:
            if discard == '':
                continue
            if discard[0] == '-':
                # remove the card from assigned discards and add back to handcards
                extracted_cards = [
                    card for card in cards if card.name == discard[1:]]
                self.handcards.extend(extracted_cards)
                while extracted_cards:
                    cards.remove(extracted_cards.pop(0))
            elif discard[0] == '*':
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

    def draw_card(self, other: Player) -> None:
        card = random.choice(other.handcards)
        other.handcards.remove(card)
        self.handcards.append(card)
        print(util.format_info(
            f'{self.name} drew {card.name} from {other.name}'))

    def order_cities(self) -> Tuple[int, int]:
        return (self.cities, self.ast_ranking)

    def order_ast_position(self) -> Tuple[int, int]:
        return (self.ast_position, self.ast_ranking)

    def order_cards_internal_value(self, card: Card) -> Tuple[int, int, int, str]:
        return (calc_card_value(card, self.handcards), calc_set_value(card, self.handcards), card.value, card.name)

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f'{self.name}'

    def print_handcards(self, preceding_str: str = '', calamities: bool = False) -> None:
        text = ''
        sorted_handcards = sorted(
            list(set(self.handcards)), key=lambda x: (x.value, calc_set_value(x, self.handcards), x.name), reverse=True)
        if not calamities:
            sorted_handcards = filter(lambda x: x.value >= 0, sorted_handcards)
        for card in sorted_handcards:
            count = self.handcards.count(card)
            text += f'{preceding_str}{"*" if count == card.max_count else " "}{card.name:<10}({card.value}): {count}/{card.max_count} cards with a set value of {calc_set_value(card, self.handcards):>3}\n'
        print(util.format_info(text))


def evaluate(cards: List[Card]) -> int:
    value = 0
    for card in filter(lambda x: x.value > 0, set(cards)):
        value = value + calc_set_value(card, cards)

    return value


def calc_card_value(card: Card, cards: List[Card]) -> float:
    count = cards.count(card)
    if count == 0:
        return 0
    if count == card.max_count:
        value = calc_set_value(card, cards)
        return int(value / count)
    # add additional card to set
    add_cards = cards.copy() + [card]
    value = calc_set_value(card, cards)
    add_value = calc_set_value(card, add_cards)
    return add_value - value


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


def without_full_sets(cards: List[Card]) -> List[Card]:
    full_sets = [card for card in set(
        cards) if cards.count(card) == card.max_count]
    filtered_cards = list(filter(lambda x: x not in full_sets, cards))
    return filtered_cards
