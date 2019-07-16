from iconservice import *

TAG = 'UseInterface'

class SampleInterface(InterfaceScore):
    @interface
    def getOwnerName(self):
        pass

class UseInterface(IconScoreBase):
    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def getOwnerName(self) -> str:
        interface = self.create_interface_score(Address.from_string("cxc5c38f4d6885e72f1466c75a35734b4676bb5acb"), SampleInterface)
        return interface.getOwnerName()


