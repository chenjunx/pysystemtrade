from sysbrokers.broker_futures_contract_price_data import brokerFuturesContractPriceData
from syscore.dateutils import Frequency
from syscore.objects import missing_contract, missing_data, failure

from sysexecution.orders.broker_orders import brokerOrder
from sysexecution.orders.contract_orders import contractOrder
from sysexecution.tick_data import dataFrameOfRecentTicks, tickerObject
from sysobjects.contract_dates_and_expiries import listOfContractDateStr
from sysobjects.contracts import futuresContract, listOfFuturesContracts
from sysobjects.dict_of_futures_per_contract_prices import dictFuturesContractPrices
from sysobjects.futures_per_contract_prices import futuresContractPrices
from syscore.dateutils import Frequency, DAILY_PRICE_FREQ
from sysbrokers.mills.mills_connection import connectionMills
from syscore.objects import missing_contract

from syslogdiag.log_to_screen import logtoscreen
from syscore.dateutils import from_config_frequency_pandas_resample

import pandas as pd
from datetime import datetime
VERY_BIG_NUMBER = 999999.0


class millsFuturesContractPriceData(brokerFuturesContractPriceData):
    def __init__(self, connection_Mills: connectionMills, log=logtoscreen("millsFuturesContractPriceData")):
        self._connection_Mills = connection_Mills
        super().__init__(log=log)

    def get_list_of_instrument_codes_with_merged_price_data(self) -> list:
        return super().get_list_of_instrument_codes_with_merged_price_data()

    def get_list_of_instrument_codes_with_price_data_at_frequency(self, frequency: Frequency) -> list:
        return super().get_list_of_instrument_codes_with_price_data_at_frequency(frequency)

    def has_merged_price_data_for_contract(self, contract_object: futuresContract) -> bool:
        return super().has_merged_price_data_for_contract(contract_object)

    def has_price_data_for_contract_at_frequency(self, contract_object: futuresContract, frequency: Frequency) -> bool:
        return super().has_price_data_for_contract_at_frequency(contract_object, frequency)

    def contracts_with_merged_price_data_for_instrument_code(self, instrument_code: str) -> listOfFuturesContracts:
        return super().contracts_with_merged_price_data_for_instrument_code(instrument_code)

    def contracts_with_price_data_at_frequency_for_instrument_code(self, instrument_code: str,
                                                                   frequency: Frequency) -> listOfFuturesContracts:
        return super().contracts_with_price_data_at_frequency_for_instrument_code(instrument_code, frequency)

    def contract_dates_with_merged_price_data_for_instrument_code(self, instrument_code: str) -> listOfContractDateStr:
        return super().contract_dates_with_merged_price_data_for_instrument_code(instrument_code)

    def contract_dates_with_price_data_at_frequency_for_instrument_code(self, instrument_code: str,
                                                                        frequency: Frequency) -> listOfContractDateStr:
        return super().contract_dates_with_price_data_at_frequency_for_instrument_code(instrument_code, frequency)

    def get_merged_prices_for_instrument(self, instrument_code: str) -> dictFuturesContractPrices:
        return super().get_merged_prices_for_instrument(instrument_code)

    def get_prices_at_frequency_for_instrument(self, instrument_code: str,
                                               frequency: Frequency) -> dictFuturesContractPrices:
        return super().get_prices_at_frequency_for_instrument(instrument_code, frequency)

    def get_merged_prices_for_contract_object(self, contract_object: futuresContract, return_empty: bool = True):
        return super().get_merged_prices_for_contract_object(contract_object, return_empty)

    def get_prices_at_frequency_for_contract_object(self, contract_object: futuresContract, frequency: Frequency,
                                                    return_empty: bool = True):
        prices = self._get_prices_at_frequency_for_contract_object_no_checking(
            contract_object=contract_object,
            freq=frequency
        )
        if prices is missing_data:
            if return_empty:
                return futuresContractPrices.create_empty()
            else:
                return missing_data

        return prices

    def write_merged_prices_for_contract_object(self, futures_contract_object: futuresContract,
                                                futures_price_data: futuresContractPrices, ignore_duplication=False):
        super().write_merged_prices_for_contract_object(futures_contract_object, futures_price_data, ignore_duplication)

    def write_prices_at_frequency_for_contract_object(self, futures_contract_object: futuresContract,
                                                      futures_price_data: futuresContractPrices, frequency: Frequency,
                                                      ignore_duplication=False):
        super().write_prices_at_frequency_for_contract_object(futures_contract_object, futures_price_data, frequency,
                                                              ignore_duplication)

    def update_prices_at_frequency_for_contract(self, contract_object: futuresContract,
                                                new_futures_per_contract_prices: futuresContractPrices,
                                                frequency: Frequency, check_for_spike: bool = True,
                                                max_price_spike: float = VERY_BIG_NUMBER) -> int:
        return super().update_prices_at_frequency_for_contract(contract_object, new_futures_per_contract_prices,
                                                               frequency, check_for_spike, max_price_spike)

    def delete_prices_at_frequency_for_contract_object(self, futures_contract_object: futuresContract,
                                                       frequency: Frequency, areyousure=False):
        return super().delete_prices_at_frequency_for_contract_object(futures_contract_object, frequency, areyousure)

    def delete_merged_prices_for_instrument_code(self, instrument_code: str, areyousure=False):
        return super().delete_merged_prices_for_instrument_code(instrument_code, areyousure)

    def delete_prices_at_frequency_for_instrument_code(self, instrument_code: str, frequency: Frequency,
                                                       areyousure=False):
        return super().delete_prices_at_frequency_for_instrument_code(instrument_code, frequency, areyousure)

    def get_contracts_with_merged_price_data(self) -> listOfFuturesContracts:
        pass

    def get_contracts_with_price_data_for_frequency(self, frequency: Frequency) -> listOfFuturesContracts:
        pass

    def _delete_prices_at_frequency_for_contract_object_with_no_checks_be_careful(self,
                                                                                  futures_contract_object: futuresContract,
                                                                                  frequency: Frequency):
        pass

    def _write_prices_at_frequency_for_contract_object_no_checking(self, futures_contract_object: futuresContract,
                                                                   futures_price_data: futuresContractPrices,
                                                                   frequency: Frequency):
        pass

    def _get_merged_prices_for_contract_object_no_checking(self,
                                                           contract_object: futuresContract) -> futuresContractPrices:
        pass

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
        # price_data = price_data.remove_zero_prices_if_zero_volumes()
        return price_data

    ## 判断期货是否存在
    def has_data_for_contract(self, contract_object: futuresContract) -> bool:
        contract_object_with_mills_data = self._connection_Mills.query_contract_info(contract_object)
        if contract_object_with_mills_data == str(missing_contract):
            return False
        else:
            return True
