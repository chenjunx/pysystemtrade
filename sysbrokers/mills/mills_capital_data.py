

from sysbrokers.broker_capital_data import brokerCapitalData
from sysbrokers.mills.mills_connection import connectionMills
from syslogdiag.log_to_screen import logtoscreen
from sysobjects.spot_fx_prices import currencyValue, listOfCurrencyValues

from syscore.constants import arg_not_supplied
import json
class millsCapitalData(brokerCapitalData):
    def __init__(
            self, connection_Mills: connectionMills, log=logtoscreen("millsCapitalData")
    ):
        super().__init__(log=log)
        self._connection_Mills = connection_Mills

    def get_account_value_across_currency(self, account_id: str = arg_not_supplied) -> listOfCurrencyValues:
        totalValues = self._connection_Mills.query_total_accout_value()
        try:
            if totalValues != 'error':
                list_of_values_per_currency = list(
                    [
                        currencyValue(
                            currency['currency'],
                            currency['value']
                           ,
                        )
                        for currency in totalValues
                    ])
                list_of_values_per_currency = listOfCurrencyValues(list_of_values_per_currency)
                return list_of_values_per_currency
            else:
                return listOfCurrencyValues()
        except BaseException:
            return listOfCurrencyValues()

    def get_excess_liquidity_value_across_currency(self, account_id: str = arg_not_supplied) -> listOfCurrencyValues:
        totalValues = self._connection_Mills.query_excess_liquidity_value_across()
        try:
            if totalValues != 'error':
                list_of_values_per_currency = list(
                    [
                        currencyValue(
                            currency['currency'],
                            currency['value']
                            ,
                        )
                        for currency in totalValues
                    ])
                list_of_values_per_currency = listOfCurrencyValues(list_of_values_per_currency)
                return list_of_values_per_currency
            else:
                return listOfCurrencyValues()
        except BaseException:
            return listOfCurrencyValues()
