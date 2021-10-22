from typing import Tuple

class Card:
    def __init__(self, name: str, value: int, max_count: int, calamity: str = None, tradeable: bool = True, offerable: bool = True) -> None:
        self.name = name
        self.value = value
        self.max_count = max_count
        self.calamity = calamity
        self.tradeable = tradeable
        self.offerable = offerable

    def is_calamity(self) -> bool:
        return self.calamity is not None

    def order_calamity(self) -> Tuple[str, int, bool]:
        return (self.calamity, self.value, not self.tradeable)

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f'{self.name}({self.value})'
