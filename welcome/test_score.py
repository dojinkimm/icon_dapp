from iconsdk.providers.http_provider import HTTPProvider
from iconsdk.icon_service import IconService
from iconsdk.builder.transaction_builder import DeployTransactionBuilder

class TestScore:
    def __init__(self):
        super().__init__()
        # YEOUIDO Tesstnet
        self.icon_service = IconService(HTTPProvider("https://bicon.net.solidwallet.io/api/v3"))

    def setUp(self):
        super.setUp()
        print('setup')

    def tearDown(self):
        print('tearDown')

    def deploy_trans(self):
        return
    