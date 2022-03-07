
from sysbrokers.broker_futures_contract_data import brokerFuturesContractData
from syscore.dateutils import listOfOpeningTimes
from sysobjects.contract_dates_and_expiries import expiryDate
from sysobjects.contracts import futuresContract


class millsFuturesContractData(brokerFuturesContractData):
    def get_actual_expiry_date_for_single_contract(self, futures_contract: futuresContract) -> expiryDate:
        pass

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