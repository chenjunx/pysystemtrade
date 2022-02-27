from syscore.objects import missing_data, arg_not_supplied

from syslogdiag.log_to_screen import logtoscreen
from sysbrokers.mills.mills_gateway import MillsGW
from sysdata.config.production_config import get_production_config
from sysbrokers.mills.mills_connection_defaults import  mills_defaults

class connectionMills(object):
    def __init__(
            self,
            mills_ipaddress: str = arg_not_supplied,
            mills_port: int = arg_not_supplied,
            account: str = arg_not_supplied,
            log=logtoscreen("connectionMills"),
    ):
        ipaddress, port, __ = mills_defaults(mills_ipaddress=mills_ipaddress, mills_port=mills_port)

        log.label(broker="mills")
        self._mills_connection_config = dict(
            ipaddress=ipaddress, port=port
        )
        self._millsGw = MillsGW()
        self._account = account
        pass

    @property
    def millsGW(self):
        return self._millsGw
    @property
    def log(self):
        return self._log

    @property
    def account(self):
        return self._account

def get_broker_account() -> str:
    production_config = get_production_config()
    account_id = production_config.get_element_or_missing_data("broker_account")
    return account_id