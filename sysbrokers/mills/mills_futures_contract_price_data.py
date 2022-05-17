from sysbrokers.broker_futures_contract_price_data import brokerFuturesContractPriceData
from syscore.dateutils import Frequency
from sysexecution.orders.broker_orders import brokerOrder
from sysexecution.orders.contract_orders import contractOrder
from sysexecution.tick_data import dataFrameOfRecentTicks, tickerObject
from sysobjects.contracts import futuresContract, listOfFuturesContracts
from sysobjects.futures_per_contract_prices import futuresContractPrices
from syscore.dateutils import Frequency, DAILY_PRICE_FREQ
from sysbrokers.mills.mills_connection import connectionMills
from syscore.objects import missing_contract

from syslogdiag.log_to_screen import logtoscreen
from syscore.dateutils import from_config_frequency_pandas_resample

import pandas as pd
from datetime import datetime
class millsFuturesContractPriceData(brokerFuturesContractPriceData):
    def __init__(self, connection_Mills: connectionMills, log=logtoscreen("millsFuturesContractPriceData")):
        self._connection_Mills = connection_Mills
        super().__init__(log=log)

    def get_prices_at_frequency_for_potentially_expired_contract_object(self, contract: futuresContract,
                                                                        freq: Frequency = DAILY_PRICE_FREQ) -> futuresContractPrices:
        pass

    def get_ticker_object_for_order(self, order: contractOrder) -> tickerObject:
        pass

    def cancel_market_data_for_order(self, order: brokerOrder):
        pass

    def get_recent_bid_ask_tick_data_for_contract_object(self,
                                                         contract_object: futuresContract) -> dataFrameOfRecentTicks:
        pass

    def _write_prices_for_contract_object_no_checking(self, *args, **kwargs):
        pass

    def delete_prices_for_contract_object(self, *args, **kwargs):
        pass

    def _delete_prices_for_contract_object_with_no_checks_be_careful(self, futures_contract_object: futuresContract):
        pass

    def get_contracts_with_price_data(self) -> listOfFuturesContracts:
        raise NotImplementedError("Do not use get_contracts_with_price_data with mills")

    def _get_prices_for_contract_object_no_checking(self, contract_object: futuresContract) -> futuresContractPrices:
        price_series = self._get_prices_at_frequency_for_contract_object_no_checking(
            contract_object, freq=DAILY_PRICE_FREQ
        )


    def _get_prices_at_frequency_for_contract_object_no_checking(self, contract_object: futuresContract,
                                                                 freq: Frequency) -> futuresContractPrices:
        new_log = contract_object.log(self.log)
        if not self.has_data_for_contract(contract_object):
            new_log.warn("Can't get data for %s" % str(contract_object))
            return futuresContractPrices.create_empty()
        resample_freq = from_config_frequency_pandas_resample(freq)
        timestr = ''
        price_data = futuresContractPrices.create_empty()
        if resample_freq == 'D':
            timestr = '%Y%m%d'
            price_data = self._connection_Mills.query_historical_futures_data_for_contract(contract_object)
        elif resample_freq == 'H':
            timestr = '%Y%m%d %H:%M:%S'
            price_data = self._connection_Mills.query_historical_futures_data_for_contract_hour(contract_object)

        if price_data == str(missing_contract):
            new_log.warn(
                "Something went wrong getting mills price data for %s"
                % str(price_data)
            )
            price_data = futuresContractPrices.create_empty()
        elif price_data == '':
            new_log.warn(
                "No mills price data found for %s"
                % str(price_data)
            )
            price_data = futuresContractPrices.create_empty()
        else:
            df = pd.read_json(price_data, encoding = "utf-8", orient = 'records')

            df['Time1'] = df['Time'].apply(
                lambda time: datetime.strptime(str(time),timestr))
            df.index = df['Time1']
            df.drop("Time", axis=1, inplace=True)
            df.drop("Time1", axis=1, inplace=True)
            price_data = futuresContractPrices(df)

        ## It's important that the data is in local time zone so that this works
        price_data = price_data.remove_future_data()

        ## Ignore zeros if no volumes (if volume could be real price eg crude oil)
        price_data = price_data.remove_zero_prices_if_zero_volumes()
        return price_data

    ## 判断期货是否存在
    def has_data_for_contract(self, contract_object: futuresContract) -> bool:
        contract_object_with_mills_data = self._connection_Mills.query_contract_info(contract_object)
        if contract_object_with_mills_data == str(missing_contract):
            return False
        else:
            return True
