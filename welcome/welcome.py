'''
iconservice, tbears가 로컬에서 설치가 되지 않고
docker image도 로딩이 매우 길고 vim도 설치 안되고
vi로 edit하려고 할 때 키가 제대로 먹히지 않았습니다.

그래서 실제로 test는 해보지 못하고 튜토리얼과 주어진 pdf를 참고해서 코드를 작성했습니다.
'''

from iconservice import *
import os

from iconsdk.builder.transaction_builder import DeployTransactionBuilder
from iconsdk.builder.call_builder import CallBuilder
from iconsdk.libs.in_memory_zip import gen_deploy_data_content
from iconsdk.signed_transaction import SignedTransaction

from tbears.libs.icon_integrate_test import IconIntegrateTestBase, SCORE_INSTALL_ADDRESS

TAG = 'Welcome'

DIR_PATH = os.path.abspath(os.path.dirname(__file__))


class Welcome(IconScoreBase):
    TEST_HTTP_ENDPOINT_URI_V3 = "http://127.0.0.1:9000/api/v3"
    SCORE_PROJECT = os.path.abspath(os.path.join(DIR_PATH, '..'))
    
    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self.wallet = KeyWallet.create()
        self.icon_service = IconService(HTTPProvider(TEST_HTTP_ENDPOINT_URI_V3))
        self.tester_addr = wallet.get_address()
        self._score_address = ""

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()

    def setUp(self):
        super().setUp()

        self.icon_service = None

        self._score_address = self._self_deploy_score()['scoreAddress']

    def tearDown(self):
        print("-" * 180)

    def _deploy_score(self, to: str = SCORE_INSTALL_ADDRESS) -> dict:
        # SCORE deploy하기 위한 transaction instance를 만든다 
        transaction = DeployTransactionBuilder() \
            .from_(self._test.get_address()) \
            .to(to) \
            .step_limit(100_000_000_000) \
            .nid(3) \
            .nonce(100) \
            .content_type("application/zip") \
            .content(gen_deploy_data_content(self.SCORE_PROJECT)) \
            .build()

        # signature 를 가진 signed transaction 리턴한다
        signed_transaction = SignedTransaction(transaction, self._test)

        # 로컬에서 transaction process 한다 
        tx_result = self.process_transaction(signed_transaction)

        self.assertTrue('status' in tx_result)
        self.assertEqual(1, tx_result['status'])
        self.assertTrue('scoreAddress' in tx_result)

        return tx_result

    def test_score_update(self):
        # SCORE 업데이트
        tx_result = self._deploy_score(self._score_address)

        self.assertEqual(self._score_address, tx_result['scoreAddress'])

    def test_call_welcome(self):
        # Call Builder로 call instance 생성
        call = CallBuilder().from_(self._test.get_address()) \
            .to(self._score_address) \
            .method("welcome") \
            .build()

        # Call request 보낸다
        response = self.process_call(call, self.icon_service)


    def test_transaction_builder(self):
        new_address = "cx0000000000000000000000000000000000000001"
        params = {"_scoreAddress": new_address}
        transaction = CallTransactionBuilder() \
            .method("setScoreAddress") \
            .params(params) \
            .step_limit(10000000000) \
            .to(self._score_address) \
            .build()

        signed_transaction = SignedTransaction(transaction, self._test)
        tx_result = self.process_transaction(signed_transaction)
        self.assertEqual(1, tx_result['status'])


    @eventlog(indexed=3)
    def ScroogeSend(self, _to: Address, _amount: int, _will_sent: int):
        pass

    @eventlog(indexed=3)
    def ScroogeGet(self, _owner: Address, _amount: int, _scrooge_get: int):
        pass

    @external(readonly=True)
    def welcome(self) -> str:
        return f"Hello, {self.msg.sender} !!! Welcome to ICON Workshop 2019!!!"

    @payable
    @external
    def scrooge(self, _to: Address, _ratio: int) -> str:

        # check sender's balance is bigger than send value
        if (self.icx.get_balance(self.msg.sender) < self.msg.value):
            self.revert(f"Hey, {self.msg.sender} !!! you have only {self.icx.get_balance(self.msg.sender)} !!!")

        # calculate scrooge's fee
        _scrooge_get = int(self.msg.value/_ratio)
        _will_sent = self.msg.value - _scrooge_get

        # send Tx
        self.icx.send(addr_to=_to, amount=_will_sent)
        self.icx.send(addr_to=self.owner, amount=_scrooge_get)

        # write to eventlog
        self.ScroogeSend(_to , self.msg.value, _will_sent)
        self.ScroogeGet(self.owner,self.msg.value, _scrooge_get)

        return "Done."


