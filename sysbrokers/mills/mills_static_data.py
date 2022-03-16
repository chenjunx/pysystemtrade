from sysbrokers.broker_static_data import brokerStaticData
from sysbrokers.mills.mills_connection import connectionMills
from syslogdiag.log_to_screen import logtoscreen
class millsStaticData(brokerStaticData):

    def __init__(
            self, connection_Mills: connectionMills, log=logtoscreen("millsStaticData")
    ):
        super().__init__(log=log)
        self._connection_Mills = connection_Mills

    def get_broker_clientid(self) -> int:
        return 0

    def get_broker_account(self) -> str:
        return "none"

    def get_broker_name(self) -> str:
        return "mills"