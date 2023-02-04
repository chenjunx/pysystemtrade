
from sysbrokers.broker_fx_handling import brokerFxHandlingData
from sysbrokers.broker_trade import brokerTrade
from sysbrokers.mills.mills_connection import connectionMills
from syslogdiag.log_to_screen import logtoscreen
from syscore.constants import arg_not_supplied

import json
class millsFxHandlingData(brokerFxHandlingData):
    def __init__(self, connection_Mills: connectionMills, log=logtoscreen("ibFXHandlingData")):
        self._connection_Mills = connection_Mills

    def broker_fx_balances(self, account_id: str = arg_not_supplied) -> dict:
        totalValues = self._connection_Mills.query_total_accout_value()
        result = dict(
            [
                (summary_item['currency'], summary_item['value'])
                for summary_item in totalValues
            ]
        )
        return result

    def broker_fx_market_order(self, trade: float, ccy1: str, account_id: str = arg_not_supplied,
                               ccy2: str = "USD") -> brokerTrade:
        pass



