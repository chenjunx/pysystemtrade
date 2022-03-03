from syscore.objects import missing_data, arg_not_supplied

from syslogdiag.log_to_screen import logtoscreen
from sysdata.config.production_config import get_production_config
from sysbrokers.mills.mills_connection_defaults import  mills_defaults

import requests
import json
import pandas as pd
class connectionMills(object):
    def __init__(
            self,
            mills_ipaddress: str = arg_not_supplied,
            mills_port: int = arg_not_supplied,
            account: str = arg_not_supplied,
            log=logtoscreen("connectionMills"),
    ):
        ipaddress, port = mills_defaults(mills_ipaddress=mills_ipaddress, mills_port=mills_port)

        log.label(broker="mills")
        self._mills_connection_config = dict(
            ipaddress=ipaddress, port=port
        )
        pass

    @property
    def log(self):
        return self._log

    #获取汇率数据
    def query_fx_Data(self):
        url = "https://v6.exchangerate-api.com/v6/25c26574f2eac4a80b0def3c/latest/USD"
        res = requests.get(url)
        print(res.text)
        jsonData = json.loads(res.text)
        return jsonData
