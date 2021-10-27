from __future__ import annotations
from typing import List, Dict, Tuple
import random
from components.card import Card
import util.texts as util


class Handcards():
    def __init__(self, cards: List[Card] = None) -> None:
        super().__init__()
        self.cards: List[Card] = cards.copy() if cards else []

    def append(self, card: Card) -> None:
        self.cards.append(card)

    def extend(self, cards: List[Card]) -> None:
        self.cards.extend(cards)

    def remove(self, card: Card) -> None:
        self.cards.remove(card)

    def filter(self, function) -> Handcards:
        return Handcards(list(filter(function, self.cards)))

    def get_card(self, index: int = 0) -> Card:
        return self.cards[index]

    def get_cards(self) -> List[Card]:
        return self.cards.copy()

    def get_random_card(self) -> Card:
        return random.choice(self.cards)

    def evaluate(self) -> int:
        value = 0
        for card in filter(lambda x: x.value > 0, set(self.cards)):
            value = value + self.set_value(card)

        return value

    def count(self) -> int:
        return len(self.cards)

    def set_value(self, card: Card) -> int:
        count = self.cards.count(card)
        return count * count * card.value

    def card_value(self, card: Card) -> float:
        count = self.cards.count(card)
        if count == 0:
            return 0
        value = self.set_value(card)
        return value / count

    def values(self) -> Dict[Card, Tuple[int, float, int]]:
        values = {}
        for card in set(self.cards):
            card_count = self.cards.count(card)
            set_value = self.set_value(card)
            card_value = self.card_value(card)

            values[card] = (set_value, card_value, card_count)
        return values

    def get_internal_value(self, card: Card) -> int:
        current_value = self.card_value(card)
        new_set = Handcards(self.get_cards() + [card])
        new_value = new_set.card_value(card)
        return new_value - current_value

    def get_lowest_value_card(self, excluded_cards: Handcards, calamity: bool = True) -> Card:
        # order handcards by internal value in desc order
        cards = filter(lambda x: x not in excluded_cards.get_cards(),
                       self.sorted_card(reverse=False))
        card = next(
            filter(
                lambda x: x.tradeable if calamity else x.value >= 0,
                [item[0] for item in cards]
            ), None
        )
        if card is None:
            return None

        self.remove(card)
        return card

    def get_card_by_value(self, value: int, excluded_cards: Handcards) -> Card:
        cards = filter(lambda x: x not in excluded_cards.get_cards(),
                       self.sorted_card(reverse=True))

        return_card = None
        for card in filter(lambda x: x.value >= 0, [item[0] for item in cards]):
            return_card = card
            if card.value >= value:
                break
        if return_card is None:
            return None

        self.remove(return_card)
        return return_card

    def discard_cards(self, discarded_cards: List[Card], preceding_str: str = '') -> None:
        print(util.format_info(self.__str__(preceding_str=preceding_str)))

        discards = input(util.format_action(
            'Please name cards you want to discard in comma-separated fashion. trailing - for whole set:\n')).split(',')
        for discard in discards:
            if discard == '':
                continue
            if discard[0] == '-':
                # get the whole set within the handcards
                extracted_cards = [
                    card for card in self.cards if card.name == discard[1:]]
                discarded_cards.extend(extracted_cards)
                self.cards = [
                    card for card in self.cards if card not in extracted_cards]
            else:
                for card in self.cards:
                    if card.name == discard:
                        self.remove(card)
                        discarded_cards.append(card)
                        break

    def reveal_calamities(self) -> List[Card]:
        calamities = list(filter(lambda x: x.is_calamity(), self.cards))
        for card in calamities:
            self.cards.remove(card)
        return calamities

    def sorted_card(self, reverse: bool = False) -> List[Card]:
        return sorted(self.values().items(), key=lambda x: (x[1][1], x[0].value), reverse=reverse)

    def sorted_set(self, reverse: bool = False) -> List[Card]:
        return sorted(list(set(self.cards)), key=lambda x: (x.value, self.set_value(x), x.name), reverse=reverse)

    def order_by_internal_value(self, card: Card) -> Tuple[int, int, int, str]:
        return (self.get_internal_value(card), self.set_value(card), card.value, card.name)

    def __str__(self, calamities: bool = False, preceding_str: str = '') -> str:
        text = ''
        sorted_handcards = self.sorted_set(reverse=True)
        if not calamities:
            sorted_handcards = filter(lambda x: x.value >= 0, sorted_handcards)
        for card in sorted_handcards:
            count = self.cards.count(card)
            text += f'{preceding_str}{"*" if count == card.max_count else " "}{card.name:<10}({card.value}): {count}/{card.max_count} cards with a set value of {self.set_value(card):>3}\n'

        return text
