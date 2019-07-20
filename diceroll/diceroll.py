from iconservice import *

TAG = 'DiceRoll'

class DiceRoll(IconScoreBase):

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()

    def _get_random(self, data: str):
        input_data = f'{self.block.timestamp}, {data}'.encode()
        hash = sha3_256(input_data)
        return int.from_bytes(hash, 'big')

    @external(readonly=True)
    def diceRoll(self, data: str) -> int:
        return self._get_random(data) % 6
