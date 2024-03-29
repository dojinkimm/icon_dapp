"""
Exception: HTTPConnectionPool(host='127.0.0.1', port=9000):
Max retries exceeded with url: /api/debug/v3 (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x10ff8ba20>:
Failed to establish a new connection: [Errno 61] Connection refused',))

이러한 명령이 떠서 deploy를 하지 못했습니다


"""
from iconservice import *

from .gameroom.gameroom import GameRoom
from .dice.dice import Dice

TAG = 'Game'


class ChipInterface(InterfaceScore):
    """
    A class contains designated methods of Chip SCORE, enable SampleGame to use methods without implementing repeatedly.
    """

    @interface
    def mint(self, _value: int):
        pass

    @interface
    def burn(self, _amount: int):
        pass

    @interface
    def balanceOf(self, _owner: Address):
        pass

    @interface
    def transfer(self, _to: Address, _value: int, _data: bytes = None):
        pass

    @interface
    def bet(self, _from: Address, _to: Address, _value: int):
        pass


class Game(IconScoreBase):
    """
    A main SCORE class for Blackjack
    """
    _TOKEN_ADDRESS = "token_address"
    _GAME_ROOM = "game_room"
    _GAME_ROOM_LIST = "game_room_list"
    _IN_GAME_ROOM = "in_game_room"
    _RESULTS = "results"
    _DICE = "dice"
    _READY = "ready"
    _GAME_START_TIME = "game_start_time"

    @eventlog(indexed=1)
    def Calculate(self, _gameRoomId: Address):
        pass

    @eventlog
    def Roll(self, _fromAddress: Address, _gameRoomId: Address):
        pass

    def on_install(self, _tokenAddress: Address) -> None:
        super().on_install()
        if _tokenAddress.is_contract:
            self._VDB_token_address.set(_tokenAddress)
        else:
            revert("Input params must be Contract Address")

    def on_update(self) -> None:
        super().on_update()
        pass

    def __init__(self, db: 'IconScoreDatabase') -> None:
        super().__init__(db)
        self._db = db
        self._VDB_token_address = VarDB(self._TOKEN_ADDRESS, db, value_type=Address)
        self._DDB_game_room = DictDB(self._GAME_ROOM, db, value_type=str)
        self._DDB_game_start_time = DictDB(self._GAME_START_TIME, db, value_type=int)
        self._DDB_in_game_room = DictDB(self._IN_GAME_ROOM, db, value_type=Address)
        self._DDB_dice = DictDB(self._DICE, db, value_type=int)
        self._DDB_ready = DictDB(self._READY, db, value_type=bool)

    @property
    def game_room_list(self):
        return ArrayDB(self._GAME_ROOM_LIST, self._db, value_type=str)

    @property
    def results(self):
        return ArrayDB(self._RESULTS, self._db, value_type=str)

    def _bet(self, bet_from: Address, amount: int):
        chip = self.create_interfasce_score(self._VDB_token_address.get(), ChipInterface)
        chip.bet(bet_from, self.address, amount)

    @external(readonly=True)
    def showGameRoomList(self) -> list:
        response = []
        game_room_list = self.game_room_list

        for game_room in game_room_list:
            game_room_dict = json_loads(game_room)
            game_room_id = game_room_dict['game_room_id']
            creation_time = game_room_dict['creation_time']
            prize_per_game = game_room_dict['prize_per_game']
            participants = game_room_dict['participants']
            room_has_vacant_seat = "is Full" if len(participants) > 1 else "has a vacant seat"
            response.append(f"{game_room_id} : ({len(participants)} / 2). The room {room_has_vacant_seat}. Prize : {prize_per_game}. Creation time : {creation_time}")

        return response

    @external(readonly=True)
    def getGameRoomStatus(self, _gameroomId: Address) -> dict:
        gameroom_dict = json_loads(self._DDB_game_room[_gameroomId])
        active = "active" if gameroom_dict["active"] else "inactive"

        participants = gameroom_dict["participants"]
        user_ready_status = [participant + " : " + str(self._DDB_ready[Address.from_string(participant)]) for participant in participants]

        response = {
            "status": active,
            "user_ready_status": user_ready_status
        }
        return response

    @external(readonly=True)
    def getUserStatus(self, _userId: Address) -> Address:
        return self._DDB_in_game_room[_userId]

    @external
    def createRoom(self, _prizePerGame: int = 10):
        # Check whether 'self.msg.sender' is now participating to game room or not
        if self._DDB_in_game_room[self.msg.sender] is not None:
            revert("You already joined to another room")

        # Check whether the chip balance of 'self.msg.sender' exceeds the prize_per_game or not
        chip = self.create_interface_score(self._VDB_token_address.get(), ChipInterface)
        if chip.balanceOf(self.msg.sender) < _prizePerGame:
            revert("Set the prize not to exceed your balance")

        # Create the game room & Get in to it & Set the prize_per_game value
        game_room = GameRoom(self.msg.sender, self.msg.sender, self.block.height, _prizePerGame)
        game_room.join(self.msg.sender)
        self._DDB_game_room[self.msg.sender] = str(game_room)

        game_room_list = self.game_room_list
        game_room_list.put(str(game_room))
        self._DDB_in_game_room[self.msg.sender] = self.msg.sender

        """새로운 dice를 선언한다"""
        new_dice = Dice()
        self._DDB_dice[self.msg.sender] = str(new_dice)


    def _crash_room(self, game_room_id: Address):
        game_room_to_crash_dict = json_loads(self._DDB_game_room[game_room_id])

        game_room_to_crash = GameRoom(Address.from_string(game_room_to_crash_dict['owner']), Address.from_string(game_room_to_crash_dict['game_room_id']), game_room_to_crash_dict['creation_time'],
                             game_room_to_crash_dict['prize_per_game'], game_room_to_crash_dict['participants'], game_room_to_crash_dict['active'])
        participants_to_escape = game_room_to_crash.participants
        for partcipant in participants_to_escape:
            self._DDB_in_game_room.remove(Address.from_string(partcipant))

        self._DDB_game_room.remove(game_room_id)
        game_room_list = list(self.game_room_list)
        game_room_list.remove(json_dumps(game_room_to_crash_dict))
        for count in range(len(self.game_room_list)):
            self.game_room_list.pop()

        for game_room in game_room_list:
            self.game_room_list.put(game_room)

    @external
    def joinRoom(self, _gameRoomId: Address):
        # Check whether the game room with game_room_id is existent or not
        if self._DDB_game_room[_gameRoomId] is "":
            revert(f"There is no game room which has equivalent id to {_gameRoomId}")

        # Check the participant is already joined to another game_room
        if self._DDB_in_game_room[self.msg.sender] is not None:
            revert(f"You already joined to another game room : {self._DDB_in_game_room[self.msg.sender]}")

        game_room_dict = json_loads(self._DDB_game_room[_gameRoomId])
        game_room = GameRoom(Address.from_string(game_room_dict['owner']), Address.from_string(game_room_dict['game_room_id']), game_room_dict['creation_time'],
                             game_room_dict['prize_per_game'], game_room_dict['participants'], game_room_dict['active'])
        game_room_list = self.game_room_list

        # Check the chip balance of 'self.msg.sender' before getting in
        chip = self.create_interface_score(self._VDB_token_address.get(), ChipInterface)
        if chip.balanceOf(self.msg.sender) < game_room.prize_per_game:
            revert(f"Not enough Chips to join this game room {_gameRoomId}. Require {game_room.prize_per_game} chips")

        # Check the game room's participants. Max : 2
        if len(game_room.participants) > 1:
            revert(f"Full : Can not join to game room {_gameRoomId}")

        # Get in to the game room
        game_room.join(self.msg.sender)
        self._DDB_in_game_room[self.msg.sender] = _gameRoomId
        self._DDB_game_room[_gameRoomId] = str(game_room)

        game_room_index_gen = (index for index in range(len(game_room_list)) if game_room.game_room_id == Address.from_string(json_loads(game_room_list[index])['game_room_id']))

        try:
            index = next(game_room_index_gen)
            game_room_list[index] = str(game_room)
        except StopIteration:
            pass

        """join 한 사람의 dice 값도 initialize한다"""
        new_dice = Dice()
        self._DDB_dice[self.msg.sender] = str(new_dice)

    @external
    def escape(self):
        # Check whether 'self.msg.sender' is now participating to game room or not
        if self._DDB_in_game_room[self.msg.sender] is None:
            revert(f'No game room to escape')

        # Retrieve the game room ID & Check the game room status
        game_room_id_to_escape = self._DDB_in_game_room[self.msg.sender]
        game_room_to_escape_dict = json_loads(self._DDB_game_room[game_room_id_to_escape])
        game_room_to_escape = GameRoom(Address.from_string(game_room_to_escape_dict['owner']), Address.from_string(game_room_to_escape_dict['game_room_id']),
                                       game_room_to_escape_dict['creation_time'], game_room_to_escape_dict['prize_per_game'],
                                       game_room_to_escape_dict['participants'], game_room_to_escape_dict['active'])

        if game_room_to_escape.active:
            revert("The game is not finalized yet.")

        # Escape from the game room
        if game_room_to_escape.owner == self.msg.sender:
            if len(game_room_to_escape.participants) == 1:
                game_room_to_escape.escape(self.msg.sender)
                self._crash_room(game_room_id_to_escape)
            else:
                revert("Owner can not escape from room which has the other participant")
        else:
            game_room_to_escape.escape(self.msg.sender)
            self._DDB_game_room[game_room_id_to_escape] = str(game_room_to_escape)

        # Set the in_game_room status of 'self.msg.sender' to None
        game_room_list = self.game_room_list
        game_room_index_gen = (index for index in range(len(game_room_list)) if game_room_to_escape.game_room_id == Address.from_string(json_loads(game_room_list[index])['game_room_id']))

        try:
            index = next(game_room_index_gen)
            game_room_list[index] = str(game_room_to_escape)
        except StopIteration:
            pass

        self._DDB_in_game_room.remove(self.msg.sender)

    def _ban(self, game_room_id: Address, participant_to_ban: Address):
        game_room_dict = json_loads(self._DDB_game_room[game_room_id])
        game_room = GameRoom(Address.from_string(game_room_dict['owner']), Address.from_string(game_room_dict['game_room_id']), game_room_dict['creation_time'],
                             game_room_dict['prize_per_game'], game_room_dict['participants'], game_room_dict['active'])
        if game_room.owner == participant_to_ban:
            # 방 폭파
            for participant in game_room.participants:
                self._DDB_in_game_room.remove(Address.from_string(participant))
                game_room.escape(Address.from_string(participant))
            self._crash_room(game_room_id)
        else:
            game_room.escape(participant_to_ban)
            self._DDB_game_room[game_room_id] = str(game_room)
            self._DDB_in_game_room.remove(participant_to_ban)
            game_room_list = self.game_room_list
            game_room_index_gen = (index for index in range(len(game_room_list)) if game_room.game_room_id == Address.from_string(json_loads(game_room_list[index])['game_room_id']))

            try:
                index = next(game_room_index_gen)
                game_room_list[index] = str(game_room)
            except StopIteration:
                pass

    def _get_random(self, data: str):
        input_data = f'{self.block.timestamp}, {data}'.encode()
        hash = sha3_256(input_data)
        return int.from_bytes(hash, 'big')

    def diceRoll(self, data: str) -> int:
        return self._get_random(data) % 6

    @external(readonly=True)
    def getChipBalance(self, _from: Address) -> int:
        chip = self.create_interface_score(self._VDB_token_address.get(), ChipInterface)
        return chip.balanceOf(_from)

    @external
    def toggleReady(self):
        if self._DDB_in_game_room[self.msg.sender] is None:
            revert("Enter the game room first.")
        if self._DDB_ready[self.msg.sender]:
            self._DDB_ready[self.msg.sender] = False
        else:
            self._DDB_ready[self.msg.sender] = True

    @external
    def gameStart(self):
        game_room_id = self._DDB_in_game_room[self.msg.sender]
        game_room_dict = json_loads(self._DDB_game_room[game_room_id])
        game_room = GameRoom(Address.from_string(game_room_dict['owner']), Address.from_string(game_room_dict['game_room_id']), game_room_dict['creation_time'],
                             game_room_dict['prize_per_game'], game_room_dict['participants'], game_room_dict['active'])
        participants = game_room.participants

        # Check the 'self.msg.sender' == game_room.owner
        if not self.msg.sender == game_room.owner:
            revert("Only owner of game room can start the game")

        if game_room.active:
            revert("The last game is still active and not finalized")

        # Check the number of participants
        if len(participants) < 2:
            revert("Please wait for a challenger to come")

        # Make sure that all the participants are ready
        for participant in participants:
            if not self._DDB_ready[Address.from_string(participant)]:
                revert(f"{participant} is not ready to play game")

        for participant in participants:
            self._bet(bet_from=Address.from_string(participant), amount=game_room.prize_per_game)

        # Game start
        game_room.game_start()
        self._DDB_game_start_time[game_room_id] = self.block.height
        self._DDB_game_room[game_room_id] = str(game_room)

        # Set ready status of both participants to False after starting the game
        for participant in participants:
            self._DDB_ready[Address.from_string(participant)] = False

    @external(readonly=True)
    def showMine(self, _from: Address) -> str:
        dice = self._DDB_dice[_from]
        return dice

    @external
    def roll(self):
        game_room_id = self._DDB_in_game_room[self.msg.sender]
        if game_room_id is None:
            revert("You are not in game")

        game_room_dict = json_loads(self._DDB_game_room[game_room_id])
        game_room = GameRoom(Address.from_string(game_room_dict['owner']), Address.from_string(game_room_dict['game_room_id']), game_room_dict['creation_time'],
                             game_room_dict['prize_per_game'], game_room_dict['participants'], game_room_dict['active'])

        # Check whether the game is in active mode or not
        if not game_room.active:
            revert("The game is now in inactive mode")

        """roll해서 숫자를 얻는다"""
        dice_dict = json_loads(self._DDB_dice[self.msg.sender])
        dice = Dice(dice_dict['value'], dice_dict['fix'])

        if dice.fix:
            revert('You already fixed your hand')

        dice.roll_dice(self.diceRoll(dice_dict['value']))
        self._DDB_dice[self.msg.sender] = str(dice)
        self.Roll(self.msg.sender, game_room_id)

        # Check whether the fix status of all participants are True. And, If participant 'dice.value' exceeds 0, finalize the game. & Game must be finalized.
        if self._check_participants_fix(game_room_id) or dice.value > 0 or self.block.height - self._DDB_game_start_time[game_room_id] > 60:
            self.calculate(game_room_id)

    def _check_participants_fix(self, game_room_id: Address) -> bool:
        game_room_dict = json_loads(self._DDB_game_room[game_room_id])
        game_room = GameRoom(Address.from_string(game_room_dict['owner']), Address.from_string(game_room_dict['game_room_id']), game_room_dict['creation_time'],
                             game_room_dict['prize_per_game'], game_room_dict['participants'], game_room_dict['active'])
        participants = game_room.participants

        for participant in participants:
            dice_dict = json_loads(self._DDB_dice[Address.from_string(participant)])
            dice = Dice(dice_dict['value'], dice_dict['fix'])
            if not dice.fix:
                return False
        return True

    def calculate(self, game_room_id: Address = None):
        self.Calculate(game_room_id)
        chip = self.create_interface_score(self._VDB_token_address.get(), ChipInterface)

        # Finalize the game
        self._game_stop(game_room_id)

        # Calculate the result
        game_room_dict = json_loads(self._DDB_game_room[game_room_id])
        game_room = GameRoom(Address.from_string(game_room_dict['owner']), Address.from_string(game_room_dict['game_room_id']), game_room_dict['creation_time'],
                             game_room_dict['prize_per_game'], game_room_dict['participants'], game_room_dict['active'])
        participants = game_room.participants
        participant_gen = (participant for participant in participants)
        first_participant = next(participant_gen)
        first_hand_dict = json_loads(self._DDB_dice[Address.from_string(first_participant)])
        first_hand = Dice(first_hand_dict['value'])
        second_participant = next(participant_gen)
        second_hand_dict = json_loads(self._DDB_dice[Address.from_string(second_participant)])
        second_hand = Dice(second_hand_dict['value'])

        results = self.results
        loser = ""
        if first_hand.value > second_hand.value:
            chip.transfer(Address.from_string(first_participant), game_room.prize_per_game * 2)
            results.put(f"{first_participant} wins against {second_participant}.")
            loser = second_participant
        elif first_hand.value < second_hand.value:
            chip.transfer(Address.from_string(second_participant), game_room.prize_per_game * 2)
            results.put(f"{second_participant} wins against {first_participant}.")
            loser = first_participant
        else:
            chip.transfer(Address.from_string(first_participant), game_room.prize_per_game)
            chip.transfer(Address.from_string(second_participant), game_room.prize_per_game)
            results.put(f"Draw!! {first_participant}, {second_participant}.")

        if loser != "" and game_room.prize_per_game > chip.balanceOf(Address.from_string(loser)):
            self._ban(game_room_id, Address.from_string(loser))

    def _game_stop(self, game_room_id):
        game_room_dict = json_loads(self._DDB_game_room[game_room_id])
        game_room = GameRoom(Address.from_string(game_room_dict['owner']), Address.from_string(game_room_dict['game_room_id']), game_room_dict['creation_time'],
                             game_room_dict['prize_per_game'], game_room_dict['participants'], game_room_dict['active'])
        game_room.game_stop()
        self._DDB_game_room[game_room_id] = str(game_room)

    @external(readonly=True)
    def getResults(self) -> list:
        return list(self.results)

    @external
    @payable
    def mintChips(self):
        chip = self.create_interface_score(self._VDB_token_address.get(), ChipInterface)
        chip.mint(self.msg.value)

    @external
    def exchange(self, amount: int):
        chip = self.create_interface_score(self._VDB_token_address.get(), ChipInterface)
        chip.burn(amount)
        self.icx.transfer(self.msg.sender, amount)
