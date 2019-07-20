from iconservice import json_dumps


class DataHandlingClass:
    def __init__(self, attr1: int, attr2: str, attr3: bool):
        self.attr1 = attr1
        self.attr2 = attr2
        self.attr3 = attr3

    def __str__(self):
        dict_to_str = {
            'attr1': self.attr1,
            'attr2': self.attr2,
            'attr3': self.attr3
        }
        return json_dumps(dict_to_str)

    def to_str(self):
        dict_to_str = {
            'attr1': self.attr1,
            'attr2': self.attr2,
            'attr3': self.attr3
        }
        return json_dumps(dict_to_str)

    # 데이터 핸들링을 위해 위에서 확인한 DataHandlingClass 에 추가할 코드
    # attr1, attr2, attr3 입력받아 클래스의 attr 수정하기
    def handle_data(self, attr1: int, attr2: str, attr3: bool):
        self.attr1 = attr1
        self.attr2 = attr2
        self.attr3 = attr3