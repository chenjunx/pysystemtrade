
from sysbrokers.broker_futures_contract_data import brokerFuturesContractData
from syscore.dateutils import listOfOpeningTimes
from sysobjects.contract_dates_and_expiries import expiryDate
from sysobjects.contracts import futuresContract
from sysbrokers.mills.mills_connection import connectionMills
from syslogdiag.log_to_screen import logtoscreen

from syscore.objects import missing_contract

class millsFuturesContractData(brokerFuturesContractData):

    def __init__(
            self, connection_Mills: connectionMills, log=logtoscreen("ibFuturesContractData")
    ):
        super().__init__(log=log)
        self._connection_Mills = connection_Mills

    def get_actual_expiry_date_for_single_contract(self, futures_contract: futuresContract) -> expiryDate:
        """
               Get the actual expiry date of a contract from mills
                从mills中获取实际的过期日期
               :param futures_contract: type futuresContract
               :return: YYYYMMDD or None
               """
        log = futures_contract.specific_log(self.log)
        if futures_contract.is_spread_contract():
            log.warn("Can't find expiry for multiple leg contract here")
            return missing_contract

        contract_object_with_mills_data = self._connection_Mills.query_contract_info(futures_contract)
        if contract_object_with_mills_data == str(missing_contract):
            return missing_contract
        # return missing_contract
        # contract_object_with_ib_data = self.get_contract_object_with_mills_data(
        #     futures_contract
        # )
        # if contract_object_with_ib_data is missing_contract:
        #     return missing_contract
        #
        # expiry_date = contract_object_with_ib_data.expiry_date
        expiry_date = expiryDate.from_str(contract_object_with_mills_data)
        return expiry_date

    def get_min_tick_size_for_contract(self, contract_object: futuresContract) -> float:
        pass

    def get_trading_hours_for_contract(self, futures_contract: futuresContract) -> \
            listOfOpeningTimes:
        pass

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