
from sysbrokers.broker_execution_stack import brokerExecutionStackData
from sysexecution.orders.base_orders import Order
from syslogdiag.log_to_screen import logtoscreen
from sysbrokers.mills.mills_connection import connectionMills
from sysexecution.orders.list_of_orders import listOfOrders
from sysexecution.orders.broker_orders import brokerOrder
from sysexecution.order_stacks.broker_order_stack import orderWithControls
from syscore.objects import missing_order, arg_not_supplied, missing_data

from  sysbrokers.mills.mills_order_with_controls import millsOrderCouldntCreateException
from sysbrokers.mills.mills_order_with_controls import millsOrderWithControls

import json
import datetime




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

    ##获取从经纪商哪里获取非历史订单
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
        raise NotImplementedError

    def match_db_broker_order_to_order_from_brokers(
        self, broker_order_to_match: brokerOrder
    ) -> brokerOrder:
        raise NotImplementedError

    def cancel_order_given_control_object(
        self, broker_orders_with_controls: orderWithControls
    ):
        raise NotImplementedError

    def cancel_order_on_stack(self, broker_order: brokerOrder):
        raise NotImplementedError

    def check_order_is_cancelled(self, broker_order: brokerOrder) -> bool:
        raise NotImplementedError

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

        raise NotImplementedError

    def modify_limit_price_given_control_object(
        self, broker_order_with_controls: orderWithControls, new_limit_price: float
    ) -> orderWithControls:
        raise NotImplementedError

    def _put_order_on_stack_no_checking(self, order: Order):

        pass



