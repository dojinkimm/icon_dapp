from iconservice import *
from .customized_class import DataHandlingClass

TAG = 'DataHandling'

class DataHandling(IconScoreBase):

    def __init__(self, db: IconScoreDatabase):
        super().__init__(db)
        self._db = db
        self._sample_dict = DictDB('sample_dict_db', db, value_type=str)

    def on_install(self, **kwargs):
        pass

    def on_update(self, **kwargs) -> None:
        pass

    # 매직메소드 __str__ 활용
    @external
    def example_set_with_magic_method(self):
        data_handling_class = DataHandlingClass(attr1=1, attr2='hello', attr3=True)
        self._sample_class['customized_class'] = str(data_handling_class)

    # 커스텀메소드 to_str 활용
    @external
    def example_set_with_custom_method(self):
        data_handling_class = DataHandlingClass(attr1=2, attr2='world', attr3=False)
        self._sample_class['customized_class'] = data_handling_class.to_str()

    # 복구를 위해 위에서 확인한 data_handling_class.py 에 추가할 코드
    # json_loads / __init__ 활용하여 클래스 데이터 복구하고, 복구된 클래스 타입 반환하기
    @external(readonly=True)
    def example_class_type(self) -> str:
        data_handling_class_str = self._sample_class['data_handling_class']
        data_handling_class_dict = json_loads(data_handling_class_str)
        data_handling_class = DataHandlingClass(data_handling_class_dict['attr1'],
                                                data_handling_class_dict['attr2'],
                                                data_handling_class_dict['attr3'])
        return str(type(data_handling_class))

    # 데이터 핸들링을 위해 위에서 확인한 data_handling_class.py 에 추가할 코드
    # 복구한 클래스의 메소드 호출하여 데이터 변경하고 데이터베이스에 저장하기
    @external
    def example_handle_data(self):
        data_handling_class_str = self._sample_class['data_handling_class']
        data_handling_class_dict = json_loads(data_handling_class_str)
        data_handling_class = DataHandlingClass(data_handling_class_dict['attr1'],
                                                data_handling_class_dict['attr2'],
                                                data_handling_class_dict['attr3'])
        self._sample_class['data_hadnling_class'] = str(data_handling_class)
