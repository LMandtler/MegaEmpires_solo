from __future__ import annotations
from typing import List, Tuple, Dict, Set
from components.card import Card
from components.handcards import Handcards
import util.texts as util
import random


class Player(object):
    def __init__(self, name: str, ast_ranking: int, handcards: List[Card]) -> None:
        self.name = name
        self.ast_ranking = ast_ranking
        self.ast_position = 0
        self.handcards = Handcards()
        self.cities: int = 0
        self.priority_threshold = None
        self.trades: Dict[int, int] = {}

    def diff_handcard_value(self, incoming: List[Card]) -> int:
        new_handcards = Handcards(self.handcards.get_cards() + incoming)

        current_value = self.handcards.evaluate()
        new_value = new_handcards.evaluate()

        return new_value - current_value

    def calc_offer(self) -> None:
        sorted_handcards = self.handcards.sorted_card()
        value_handcards = self.handcards.evaluate()

        self.priority: Set[Card] = set()
        self.offer: List[Card] = []

        rolling_sum = 0
        for item in filter(lambda x: x[0].tradeable, sorted_handcards):
            self.priority.add(item[0])
            rolling_sum += item[1][0]

            if rolling_sum >= value_handcards * self.priority_threshold:
                break

        self.offer = list(filter(lambda x: x.offerable, self.handcards.get_cards()))

        self.offer.sort(key=lambda x: x.value, reverse=True)

    def evaluate_offer(self, other: Player) -> Tuple[Player, List[Card], List[Card], int]:
        if self.handcards.count() < 3 or other.handcards.count() < 3:
            return None

        gain_options = sorted([
            card for card in other.offer
            if card in self.priority and card not in other.priority
        ], key=lambda x: self.handcards.order_by_internal_value(x), reverse=True)
        give_options = sorted([
            card for card in self.offer
            if card in other.priority and card not in gain_options
        ], key=lambda x: other.handcards.order_by_internal_value(x), reverse=True)

        gain_value = sum([self.handcards.get_internal_value(card)
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
                    self.handcards.get_cards()
                ), key=lambda x: other.handcards.order_by_internal_value(x),
                reverse=True
            )

        # Man hat sich gefunden, indem die Prios übereinstimmen. Jetzt wird der konkrete Handel besprochen.
        # Dafür werden abwechselnd Karten benannt, die abgegeben werden und dem anderen Spieler bestmöglich helfen.
        gain = Handcards()
        give = Handcards()

        if gain_options[0].value < give_options[0].value:
            # den Handel umdrehen. Das heißt, vom anderen Spieler aus aufrufen.
            # Dann brauche ich die Logik nur einmal und muss nicht viele if/else haben
            return other.trade((self, give_options, gain_options,
                                None))

        # Die Karten werden nach dem Schema A B B A hinzugefügt.
        # Der größere Wert beginnt. Das heißt Self beginnt eine Karte zu bekommen.
        gain.append(gain_options.pop(0))
        other.handcards.remove(gain.get_card())
        give.append(give_options.pop(0))
        self.handcards.remove(give.get_card())

        if give_options:
            # give_options hat noch etwas, dann wird das auf jeden Fall gegeben, damit der geringere Wert ausgeglichen wird.
            give.append(give_options.pop(0))
            self.handcards.remove(give.get_card(1))
            # Abhängig von der Differenz
            diff = give.evaluate() - gain.evaluate()
            if diff > 0:
                gain.append(other.handcards.get_card_by_value(diff, give))
            else:
                gain.append(other.handcards.get_lowest_value_card(give, calamity=False))
        else:
            # give_options hat nichts mehr, dann wird gain mit einer niedrigwertigen Karte aufgefüllt.
            gain.append(other.handcards.get_lowest_value_card(give, calamity=False))
            if None in gain.get_cards() or None in give.get_cards():
                self.cleanup_trade(give.get_cards())
                other.cleanup_trade(gain.get_cards())
                return False
            diff = gain.evaluate() - give.evaluate()
            # Anschließend versucht give zu matchen
            give.append(self.handcards.get_card_by_value(diff, gain))

        if None in gain.get_cards() or None in give.get_cards():
            self.cleanup_trade(give)
            other.cleanup_trade(gain)
            return False

        return self.fulfill_trade(other, gain, give)

    def fulfill_trade(self, other: Player, gain: List[Card], give: List[Card]) -> bool:
        give.append(self.handcards.get_lowest_value_card(Handcards()))
        gain.append(other.handcards.get_lowest_value_card(Handcards()))
        if None in gain.get_cards() or None in give.get_cards():
            self.cleanup_trade(give.get_cards())
            other.cleanup_trade(gain.get_cards())
            return False
        # diff_self = self.diff_handcard_value(gain)
        # diff_other = other.diff_handcard_value(give)
        self.handcards.extend(gain.get_cards())
        other.handcards.extend(give.get_cards())

        self.track_last_owner(give.get_cards())
        other.track_last_owner(gain.get_cards())
        # print(self, other, gain, give, evaluate(gain), evaluate(give), diff_self, diff_other)
        self.calc_offer()
        other.calc_offer()
        return True

    def cleanup_trade(self, cards: List[Card]) -> None:
        self.handcards.extend(filter(lambda x: x is not None, cards))

    def track_last_owner(self, cards: List[Card]) -> None:
        for card in filter(lambda x: x.is_calamity(), cards):
            card.last_owner = self

    def ascend(self) -> None:
        self.ast_position += 1

    def discard_cards(self, discarded_cards: List[Card], preceding_str: str = '') -> None:
        self.handcards.discard_cards(discarded_cards, preceding_str)

    def reveal_calamities(self) -> List[Card]:
        return self.handcards.reveal_calamities()

    def draw_card(self, other: Player, trailing_str: str = '') -> None:
        card = other.handcards.get_random_card()
        other.handcards.remove(card)
        self.handcards.append(card)
        print(util.format_info(
            f'{self.name} drew {card.name} from {other.name}'))

    def order_cities(self) -> Tuple[int, int]:
        return (self.cities, self.ast_ranking)

    def order_ast_position(self) -> Tuple[int, int]:
        return (self.ast_position, self.ast_ranking)

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f'{self.name}'

    def print_handcards(self, preceding_str: str = '', calamities: bool = False) -> None:
        print(util.format_info(self.handcards))
