
from sysbrokers.broker_instrument_data import brokerFuturesInstrumentData

class millsFuturesInstrumentData(brokerFuturesInstrumentData):
    def get_brokers_instrument_code(self, instrument_code: str) -> str:
        pass

    def get_instrument_code_from_broker_code(self, broker_code: str) -> str:
        pass

    def get_list_of_instruments(self) -> list:
        pass