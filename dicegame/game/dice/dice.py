from iconservice import *


class Dice:

    def __init__(self, value: int = 0, fix: bool = False):
        if value != 0:
            self.value = value
        else:
            self.value = 0
        self.fix = fix

    def __str__(self):
        response = {
            'value': self.value,
            'fix': self.fix
        }
        return json_dumps(response)

    def roll_dice(self, value):
        self.value += value
        self.fix = True



