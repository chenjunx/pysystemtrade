
from sysbrokers.broker_contract_position_data import brokerContractPositionData
from sysobjects.production.positions import listOfContractPositions

from syscore.constants import arg_not_supplied
from sysbrokers.mills.mills_connection import connectionMills
from syslogdiag.log_to_screen import logtoscreen
from sysobjects.production.positions import contractPosition, listOfContractPositions
from sysobjects.contracts import futuresContract

import json
class millsContractPositionData(brokerContractPositionData):
    def __init__(self, millsconnection: connectionMills, log=logtoscreen("millsContractPositionData")):
        self._millsconnection = millsconnection
        super().__init__(log=log)

    def get_all_current_positions_as_list_with_contract_objects(self,
                                                                account_id=arg_not_supplied) -> listOfContractPositions:
        raw_datas = self._millsconnection.query_posistions()
        pos = []
        for raw_data in raw_datas:
            contract = futuresContract(raw_data['symbol'], raw_data['expiry'])
            contract_position_object = contractPosition(raw_data['position'], contract)
            pos.append(contract_position_object)
        list_of_contract_positions = listOfContractPositions(pos)
        list_of_contract_positions_no_duplicates = (
            list_of_contract_positions.sum_for_contract()
        )
        return list_of_contract_positions_no_duplicates

    def get_position_as_df_for_contract_object(self, *args, **kwargs):
        return super().get_position_as_df_for_contract_object(*args, **kwargs)

    def update_position_for_contract_object(self, *args, **kwargs):
        return super().update_position_for_contract_object(*args, **kwargs)

    def delete_last_position_for_contract_object(self, *args, **kwargs):
        return super().delete_last_position_for_contract_object(*args, **kwargs)

    def _get_series_for_args_dict(self, *args, **kwargs):
        return super()._get_series_for_args_dict(*args, **kwargs)

    def _update_entry_for_args_dict(self, *args, **kwargs):
        return super()._update_entry_for_args_dict(*args, **kwargs)

    def _delete_last_entry_for_args_dict(self, *args, **kwargs):
        return super()._delete_last_entry_for_args_dict(*args, **kwargs)

    def _get_list_of_args_dict(self) -> list:
        return super()._get_list_of_args_dict()

    def get_list_of_instruments_with_any_position(self):
        return super().get_list_of_instruments_with_any_position()