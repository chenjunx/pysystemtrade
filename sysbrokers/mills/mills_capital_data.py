

from sysbrokers.broker_capital_data import brokerCapitalData
from sysobjects.spot_fx_prices import listOfCurrencyValues
from sysbrokers.mills.mills_connection import connectionMills
from syslogdiag.log_to_screen import logtoscreen

from syscore.objects import arg_not_supplied

class millsCapitalData(brokerCapitalData):
    def __init__(
            self, connection_Mills: connectionMills, log=logtoscreen("millsCapitalData")
    ):
        super().__init__(log=log)
        self._connection_Mills = connection_Mills

    def get_account_value_across_currency(self, account_id: str = arg_not_supplied) -> listOfCurrencyValues:

        pass

    def get_excess_liquidity_value_across_currency(self, account_id: str = arg_not_supplied) -> listOfCurrencyValues:
        pass