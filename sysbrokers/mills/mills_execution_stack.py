
from sysbrokers.broker_execution_stack import brokerExecutionStackData
from syslogdiag.log_to_screen import logtoscreen
from sysbrokers.mills.mills_connection import connectionMills
from syscore.objects import missing_order, failure, success, arg_not_supplied
from sysexecution.orders.list_of_orders import listOfOrders
from sysexecution.orders.broker_orders import brokerOrder
from sysexecution.order_stacks.broker_order_stack import orderWithControls
import json

class millsExecutionStackData(brokerExecutionStackData):
    def __init__(self,connection_Mills: connectionMills, log=logtoscreen("millsExecutionStackData")):
        super().__init__(log=log)
        self._connection_Mills = connection_Mills

    ##获取从经纪商哪里获取非历史订单
    def get_list_of_broker_orders_with_account_id(
        self, account_id: str = arg_not_supplied
    ) -> listOfOrders:
        orders_str = self._connection_Mills.query_active_orders()
        orders = json.loads(orders_str)
        new_orders = []
        for order in orders:
            v_rokerOrder = brokerOrder(fill_datetime=order['datetime'],
                                      key= order['id'],
                                      order_id=order['id'],
                                      filled_price=order['info']['avgFillPrice'],
                                      fill=order['filled'],
                                      trade=order['amount'],
                                       commission=order['fee'])
            new_orders.append(v_rokerOrder)
        order_list = listOfOrders(new_orders)
        return order_list

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
        raise NotImplementedError

    def check_order_can_be_modified_given_control_object(
        self, broker_order_with_controls: orderWithControls
    ) -> bool:

        raise NotImplementedError

    def modify_limit_price_given_control_object(
        self, broker_order_with_controls: orderWithControls, new_limit_price: float
    ) -> orderWithControls:
        raise NotImplementedError
