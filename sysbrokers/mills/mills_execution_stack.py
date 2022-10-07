
from sysbrokers.broker_execution_stack import brokerExecutionStackData
from sysexecution.orders.base_orders import Order
from syslogdiag.log_to_screen import logtoscreen
from sysbrokers.mills.mills_connection import connectionMills
from sysexecution.orders.list_of_orders import listOfOrders
from sysexecution.orders.broker_orders import brokerOrder
from sysexecution.order_stacks.broker_order_stack import orderWithControls
from syscore.objects import missing_order, arg_not_supplied, missing_data,failure,success

from  sysbrokers.mills.mills_order_with_controls import millsOrderCouldntCreateException
from sysbrokers.mills.mills_order_with_controls import millsOrderWithControls

import json


def match_control_order_from_dict(
    dict_of_broker_control_orders: dict, broker_order_to_match: brokerOrder
):

    matched_control_order_from_dict = dict_of_broker_control_orders.get(
        broker_order_to_match.broker_tempid, missing_order
    )

    return matched_control_order_from_dict



class millsExecutionStackData(brokerExecutionStackData):
    def __init__(self,connection_Mills: connectionMills, log=logtoscreen("millsExecutionStackData")):
        super().__init__(log=log)
        self._connection_Mills = connection_Mills

    def put_order_on_stack(self, new_order: Order):
        trade_with_contract_from_mills = json.loads(self._connection_Mills.place_order(new_order))
        if trade_with_contract_from_mills is missing_order:
            return missing_order

        placed_broker_order_with_controls = millsOrderWithControls(
            trade_with_contract_from_mills,
            broker_order=new_order,
            connectionMills=self._connection_Mills
        )

        # We do this so we can cancel stuff and get things back more easily
        self._add_order_with_controls_to_store(placed_broker_order_with_controls)

        return placed_broker_order_with_controls

    def _add_order_with_controls_to_store(
        self, order_with_controls: millsOrderWithControls
    ):
        storage_key = order_with_controls.order.broker_tempid
        self.traded_object_store[storage_key] = order_with_controls


    @property
    def traded_object_store(self) -> dict:
        store = getattr(self, "_traded_object_store", None)
        if store is None:
            store = self._traded_object_store = {}

        return store

    ##获取从经纪商哪里获取24小时以内的历史订单
    def get_list_of_broker_orders_with_account_id(
        self, account_id: str = arg_not_supplied
    ) -> listOfOrders:
        list_of_control_objects = self._get_list_of_broker_control_orders(
        )
        order_list = [
            order_with_control.order for order_with_control in list_of_control_objects
        ]

        order_list = listOfOrders(order_list)
        return order_list

    def _get_list_of_broker_control_orders(
            self, account_id: str = arg_not_supplied
    ) -> list:
        """
        Get list of broker orders from IB, and return as list of orders with controls

        :return: list of brokerOrder objects
        """
        orders_str = self._connection_Mills.query_active_orders()
        list_of_raw_orders_as_trade_objects = json.loads(orders_str)

        broker_order_with_controls_list = [
            self._create_broker_control_order_object(broker_trade_object_results)
            for broker_trade_object_results in list_of_raw_orders_as_trade_objects
        ]

        broker_order_with_controls_list = [
            broker_order_with_controls
            for broker_order_with_controls in broker_order_with_controls_list
            if broker_order_with_controls is not missing_order
        ]

        return broker_order_with_controls_list


    def _create_broker_control_order_object(
        self, order
    ):
        """
        Map from the data mills gives us to my broker order object, to order with controls

        :param trade_with_contract_from_ib: tradeWithContract
        :return: brokerOrder
        """
        try:

            instrument_code = order['instrument_code']
            broker_order_with_controls = millsOrderWithControls(
                order,
                instrument_code=instrument_code,
            )
            return broker_order_with_controls
        except millsOrderCouldntCreateException:
            self.log.warn(
                "Couldn't create order from mills returned order %s, usual behaviour for FX and equities trades"
                % str(order)
            )
            return missing_order



    def get_list_of_orders_from_storage(self) -> listOfOrders:
        dict_of_stored_orders = self._get_dict_of_orders_from_storage()
        list_of_orders = listOfOrders(dict_of_stored_orders.values())

        return list_of_orders

    def match_db_broker_order_to_order_from_brokers(
        self, broker_order_to_match: brokerOrder
    ) -> brokerOrder:
        matched_control_order = (
            self.match_db_broker_order_to_control_order_from_brokers(
                broker_order_to_match
            )
        )
        if matched_control_order is missing_order:
            return missing_order

        broker_order = matched_control_order.order

        return broker_order

    def match_db_broker_order_to_control_order_from_brokers(
        self, broker_order_to_match: brokerOrder
    ) -> millsOrderWithControls:
        """

        :return: brokerOrder coming from broker
        """

        # check stored orders first
        dict_of_stored_control_orders = self._get_dict_of_control_orders_from_storage()
        matched_control_order = match_control_order_from_dict(
            dict_of_stored_control_orders, broker_order_to_match
        )
        if matched_control_order is not missing_order:
            return matched_control_order

        # try getting from broker
        # match on temp id and clientid
        dict_of_broker_control_orders = self._get_dict_of_broker_control_orders(
        )
        matched_control_order = match_control_order_from_dict(
            dict_of_broker_control_orders, broker_order_to_match
        )
        if matched_control_order is not missing_order:
            matched_control_order.order.parent = broker_order_to_match.parent
            return matched_control_order

        return matched_control_order

    def _get_dict_of_broker_control_orders(
        self
    ) -> dict:
        control_order_list = self._get_list_of_broker_control_orders(
        )
        dict_of_control_orders = dict(
            [
                (control_order.order.broker_tempid, control_order)
                for control_order in control_order_list
            ]
        )
        return dict_of_control_orders

    def cancel_order_given_control_object(
        self, broker_orders_with_controls: orderWithControls
    ):
        self._connection_Mills.cancel_order(broker_orders_with_controls.order)
        return success


    def cancel_order_on_stack(self, broker_order: brokerOrder):
        log = broker_order.log_with_attributes(self.log)
        matched_control_order = (
            self.match_db_broker_order_to_control_order_from_brokers(broker_order)
        )
        if matched_control_order is missing_order:
            log.warn("Couldn't cancel non existent order")
            return None

        self.cancel_order_given_control_object(matched_control_order)
        log.msg("Sent cancellation for %s" % str(broker_order))

    def check_order_is_cancelled(self, broker_order: brokerOrder) -> bool:
        trade_with_contract_from_mills = json.loads(
            self._connection_Mills.get_order_by_id(broker_order))
        ##todo 查询订单是否已取消
        if trade_with_contract_from_mills['status'] == 'closed' and \
                float(trade_with_contract_from_mills['filled']) == 0.0:
            return True
        else:
            return False

    def check_order_is_cancelled_given_control_object(
        self, broker_order_with_controls: orderWithControls
    ) -> bool:
        trade_with_contract_from_mills = json.loads(self._connection_Mills.get_order_by_id(broker_order_with_controls.order))
        ##todo 查询订单是否已取消
        if trade_with_contract_from_mills['status']=='closed' and \
                float(trade_with_contract_from_mills['filled']) == 0.0:
            return True
        else:
            return False

    def check_order_can_be_modified_given_control_object(
        self, broker_order_with_controls: orderWithControls
    ) -> bool:
        trade_with_contract_from_mills = json.loads(self._connection_Mills.get_order_by_id(broker_order_with_controls.order))
        if trade_with_contract_from_mills['info']['status']=='closed':
            return False
        else:
            return True


    def modify_limit_price_given_control_object(
        self, broker_order_with_controls: orderWithControls, new_limit_price: float
    ) -> orderWithControls:
        broker_order_with_controls.order.limit_price = new_limit_price
        trade_with_contract_from_mills = self._connection_Mills.place_order(broker_order_with_controls.order)
        broker_order_with_controls.order.broker_tempid = json.loads(trade_with_contract_from_mills)['id']
        broker_order_with_controls.update_order()
        return broker_order_with_controls

    def _put_order_on_stack_no_checking(self, order: Order):

        pass


    def _get_dict_of_orders_from_storage(self) -> dict:
        # Get dict from storage, update, return just the orders
        dict_of_orders_with_control = self._get_dict_of_control_orders_from_storage()
        order_dict = dict(
            [
                (key, order_with_control.order)
                for key, order_with_control in dict_of_orders_with_control.items()
            ]
        )

        return order_dict

    def _get_dict_of_control_orders_from_storage(self) -> dict:
        dict_of_orders_with_control = self.traded_object_store
        __ = [
            order_with_control.update_order()
            for order_with_control in dict_of_orders_with_control.values()
        ]

        return dict_of_orders_with_control
