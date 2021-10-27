from typing import Tuple


class Card():
    def __init__(self, name: str, value: int, max_count: int, additional_set: bool, calamity: str = None, tradeable: bool = True, offerable: bool = True) -> None:
        self.name = name
        self.value = value
        self.max_count = max_count
        self.calamity = calamity
        self.tradeable = tradeable
        self.offerable = offerable
        self.additional_set = additional_set
        self.last_owner = None

    def is_commodity(self) -> bool:
        return not self.is_calamity()

    def is_calamity(self) -> bool:
        return self.calamity is not None

    def is_major_calamity(self) -> bool:
        return self.calamity == 'major'

    def is_minor_calamity(self) -> bool:
        return self.calamity == 'minor'

    def is_tradeable(self) -> bool:
        return self.tradeable

    def is_additional_set(self) -> bool:
        return self.additional_set

    def order_calamity(self) -> Tuple[str, int, bool]:
        return (self.calamity, self.value, not self.tradeable)

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f'{self.name}({self.value})'
