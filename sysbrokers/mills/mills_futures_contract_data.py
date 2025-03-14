from sysbrokers.broker_futures_contract_data import brokerFuturesContractData
from sysobjects.contract_dates_and_expiries import expiryDate
from sysobjects.contracts import futuresContract
from sysbrokers.mills.mills_connection import connectionMills
from syslogdiag.log_to_screen import logtoscreen
from sysobjects.production.trading_hours.trading_hours import tradingHours, listOfTradingHours
from syscore.exceptions import missingContract

import datetime

NO_ADJUSTMENTS = 0, 0
CLOSED_ALL_DAY = object()

missing_contract = 'missing contract'

from syslogging.logger import *


def parse_trading_hours_string(
        trading_hours_string: str,
        adjustment_hours: int = 0,
        one_off_adjustment: tuple = NO_ADJUSTMENTS,
) -> listOfTradingHours:
    day_by_day = trading_hours_string.split(";")
    list_of_open_times = [
        parse_trading_for_day(
            string_for_day,
            adjustment_hours=adjustment_hours,
            one_off_adjustment=one_off_adjustment,
        )
        for string_for_day in day_by_day
    ]

    list_of_open_times = [
        open_time for open_time in list_of_open_times if open_time is not CLOSED_ALL_DAY
    ]

    list_of_open_times = listOfTradingHours(list_of_open_times)

    return list_of_open_times

def parse_trading_for_day(
        string_for_day: str,
        adjustment_hours: int = 0,
        one_off_adjustment: tuple = NO_ADJUSTMENTS,
) -> listOfTradingHours:
    start_and_end = string_for_day.split("-")
    if len(start_and_end) == 1:
        # closed
        return CLOSED_ALL_DAY

    start_phrase = start_and_end[0]
    end_phrase = start_and_end[1]

    # Doesn't deal with DST. We will be conservative and only trade 1 hour
    # after and 1 hour before
    # adjust_start = 1 + one_off_adjustment[0]
    # adjust_end = -1 + one_off_adjustment[-1]

    start_dt = parse_phrase(
        start_phrase
    )

    end_dt = parse_phrase(
        end_phrase
    )

    return tradingHours(start_dt, end_dt)

def parse_phrase(phrase: str, adjustment_hours: int = 0, additional_adjust: int = 0)\
        -> datetime.datetime:
    total_adjustment = adjustment_hours + additional_adjust
    original_time = datetime.datetime.strptime(phrase, "%Y%m%d:%H%M")
    adjustment = datetime.timedelta(hours=total_adjustment)

    return original_time + adjustment
from sysdata.data_blob import dataBlob

class millsFuturesContractData(brokerFuturesContractData):


    def __init__(
            self, connection_Mills: connectionMills, data:dataBlob,log=get_logger("millsFuturesContractData")
    ):
        super().__init__(log=log,data=data)
        self._connection_Mills = connection_Mills

    def get_actual_expiry_date_for_single_contract(self, futures_contract: futuresContract) -> expiryDate:
        """
               Get the actual expiry date of a contract from mills
                从mills中获取实际的过期日期
               :param futures_contract: type futuresContract
               :return: YYYYMMDD or None
               """
        if futures_contract.is_spread_contract():
            self.log.warn("Can't find expiry for multiple leg contract here")
            raise missingContract

        contract_object_with_mills_data = self._connection_Mills.query_contract_info(futures_contract)
        if contract_object_with_mills_data == missing_contract:
            raise missingContract
        # return missingContract
        # contract_object_with_ib_data = self.get_contract_object_with_mills_data(
        #     futures_contract
        # )
        # if contract_object_with_ib_data is missingContract:
        #     return missingContract
        #
        # expiry_date = contract_object_with_ib_data.expiry_date
        expiry_date = expiryDate.from_str(contract_object_with_mills_data)
        return expiry_date

    def get_min_tick_size_for_contract(self, contract_object: futuresContract) -> float:
        retData = self._connection_Mills.query_min_tick_size(contract_object)
        if retData == missing_contract:
            raise missingContract
        else:
            return float(retData)



    def get_trading_hours_for_contract(self, futures_contract: futuresContract) -> \
            listOfTradingHours:
        """

         :param futures_contract:
         :return: list of paired date times
         """

        contract_object_with_mills_data = self._connection_Mills.query_contract_info(futures_contract)
        if contract_object_with_mills_data == missing_contract:
            self.log.msg("Can't resolve contract")
            return missingContract
        trading_hours = self._connection_Mills.query_trading_hours(futures_contract)

        if trading_hours == missing_contract:
            self.log.msg("No mills expiry date found")
            trading_hours = []

        trading_hours =parse_trading_hours_string(trading_hours)

        return trading_hours



    def get_list_of_contract_dates_for_instrument_code(self, instrument_code: str):
        pass

    def get_all_contract_objects_for_instrument_code(self, *args, **kwargs):
        pass

    def _get_contract_data_without_checking(self, instrument_code: str, contract_date: str) -> futuresContract:
        pass

    def is_contract_in_data(self, *args, **kwargs):
        pass

    def _delete_contract_data_without_any_warning_be_careful(self, instrument_code: str, contract_date: str):
        pass

    def _add_contract_object_without_checking_for_existing_entry(self, contract_object: futuresContract):
        pass