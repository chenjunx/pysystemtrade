from syscore.objects import missing_data, arg_not_supplied

from syslogdiag.log_to_screen import logtoscreen

from sysdata.config.production_config import get_production_config
from sysbrokers.mills.mills_connection_defaults import  mills_defaults

class connectionMills(object):
    def __init__(
            self,
            ib_ipaddress: str = arg_not_supplied,
            ib_port: int = arg_not_supplied,
            account: str = arg_not_supplied,
            log=logtoscreen("connectionMills"),
    ):
        ipaddress, port, __ = mills_defaults(ib_ipaddress=ib_ipaddress, ib_port=ib_port)

        log.label(broker="mills")
        self._ib_connection_config = dict(
            ipaddress=ipaddress, port=port
        )
        pass
