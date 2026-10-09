
from sysbrokers.broker_execution_stack import brokerExecutionStackData
from sysexecution.orders.base_orders import Order
from syslogdiag.log_to_screen import logtoscreen
from sysbrokers.mills.mills_connection import (
    connectionMills,
    millsOrderStateUnknown,
    millsRequestError,
)
from sysexecution.orders.list_of_orders import listOfOrders
from sysexecution.orders.broker_orders import brokerOrder
from sysexecution.order_stacks.broker_order_stack import orderWithControls
from sysexecution.orders.named_order_objects import missing_order
from syscore.constants import arg_not_supplied, success
from syscore.exceptions import orderCannotBeModified

from  sysbrokers.mills.mills_order_with_controls import millsOrderCouldntCreateException
from sysbrokers.mills.mills_order_with_controls import (
    millsOrderWithControls,
    ORDER_QUERY_MIN_INTERVAL_SECONDS,
)

import json

# 网关的委托状态只有 open / close
MILLS_ORDER_CLOSED_STATUS = ("close", "closed")
MILLS_ORDER_OPEN_STATUS = "open"


def is_mills_order_cancelled(trade_with_contract_from_mills: dict, broker_order: brokerOrder) -> bool:
    # 对应 IB 的 "Cancelled"：委托已关闭但没有全部成交
    # 委托量用我们自己的 broker order，不用网关的 amount（改价后的替代单 amount 可能只是剩余量）
    order_is_closed = trade_with_contract_from_mills['status'] in MILLS_ORDER_CLOSED_STATUS
    filled_abs_qty = abs(float(trade_with_contract_from_mills['filled']))
    fully_filled = filled_abs_qty >= broker_order.trade.total_abs_qty()

    return order_is_closed and not fully_filled


def match_control_order_from_dict(
    dict_of_broker_control_orders: dict, broker_order_to_match: brokerOrder
):

    matched_control_order_from_dict = dict_of_broker_control_orders.get(
        broker_order_to_match.broker_tempid, missing_order
    )

    return matched_control_order_from_dict
from sysdata.data_blob import dataBlob

class millsExecutionStackData(brokerExecutionStackData):
    def __init__(self,connection_Mills: connectionMills,data:dataBlob, log=logtoscreen("millsExecutionStackData")):
        super().__init__(log=log,data=data)
        self._connection_Mills = connection_Mills

    def put_order_on_stack(self, new_order: Order):
        try:
            trade_with_contract_from_mills = self._connection_Mills.place_order(new_order)
        except millsOrderStateUnknown as e:
            self.log.critical(
                "下单结果未知，可能已经下出，需人工核对 %s: %s" % (str(new_order), str(e)),
                **new_order.log_attributes(),
                method="temp",
            )
            raise
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
        list_of_raw_orders_as_trade_objects = self._connection_Mills.query_active_orders()

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
                connectionMills=self._connection_Mills,
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
        # 按 tempid 直接查网关（改价后网关会落到替代链上最新的委托）
        # 不用 GET /order：它只返回 active 委托，进程重启后已成交的委托永远匹配不上
        try:
            trade_with_contract_from_mills = self._connection_Mills.get_order_by_id(
                broker_order_to_match
            )
        except millsOrderStateUnknown as e:
            self.log.warning(
                "Can't match order %s, order state unknown: %s"
                % (str(broker_order_to_match), str(e)),
                **broker_order_to_match.log_attributes(),
                method="temp",
            )
            return missing_order

        matched_control_order = millsOrderWithControls.from_db_broker_order(
            broker_order_to_match,
            trade_with_contract_from_mills,
            connectionMills=self._connection_Mills,
        )

        return matched_control_order

    def cancel_order_given_control_object(
        self, broker_orders_with_controls: orderWithControls
    ):
        try:
            self._connection_Mills.cancel_order(broker_orders_with_controls.order)
        except millsOrderStateUnknown as e:
            self.log.critical(
                "撤单结果未知，需人工核对 %s: %s"
                % (str(broker_orders_with_controls.order), str(e)),
                **broker_orders_with_controls.order.log_attributes(),
                method="temp",
            )
            raise

        return success


    def cancel_order_on_stack(self, broker_order: brokerOrder):
        log_attrs = {**broker_order.log_attributes(), "method": "temp"}
        matched_control_order = (
            self.match_db_broker_order_to_control_order_from_brokers(broker_order)
        )
        if matched_control_order is missing_order:
            self.log.warning("Couldn't cancel non existent order", **log_attrs)
            return None

        try:
            self.cancel_order_given_control_object(matched_control_order)
        except millsRequestError as e:
            # 收盘撤单不能因为单张委托中断；撤没撤掉由 check_order_is_cancelled 判断并告警
            self.log.warning(
                "Couldn't cancel order %s: %s" % (str(broker_order), str(e)),
                **log_attrs,
            )
            return None
        self.log.info("Sent cancellation for %s" % str(broker_order), **log_attrs)

    def check_order_is_cancelled(self, broker_order: brokerOrder) -> bool:
        try:
            trade_with_contract_from_mills = self._connection_Mills.get_order_by_id(
                broker_order,
                max_age_seconds=ORDER_QUERY_MIN_INTERVAL_SECONDS,
            )
        except millsOrderStateUnknown as e:
            # 不能抛 missingOrder：上层会把它当成已撤单，进而按成交 0 完成订单
            # 返回 False，超时后由 critical_cancel_log 告警
            self.log.warning(
                "Order %s state unknown, treat as not cancelled: %s"
                % (str(broker_order), str(e)),
                **broker_order.log_attributes(),
                method="temp",
            )
            return False

        return is_mills_order_cancelled(trade_with_contract_from_mills, broker_order)

    def check_order_is_cancelled_given_control_object(
        self, broker_order_with_controls: millsOrderWithControls
    ) -> bool:
        trade_with_contract_from_mills = broker_order_with_controls.get_order_from_broker()

        return is_mills_order_cancelled(
            trade_with_contract_from_mills, broker_order_with_controls.order
        )

    def modify_limit_price_given_control_object(
        self, broker_order_with_controls: millsOrderWithControls, new_limit_price: float
    ) -> millsOrderWithControls:
        ## throws orderCannotBeModified
        self.check_order_can_be_modified_given_control_object_throw_error_if_not(
            broker_order_with_controls
        )

        order = broker_order_with_controls.order
        original_limit_price = order.limit_price
        order.limit_price = new_limit_price
        try:
            trade_with_contract_from_mills = self._connection_Mills.place_order(order)
        except millsOrderStateUnknown as e:
            # 例如 10004 改价时撤单超时：原委托是否还在不确定，交给下一轮 update_order 去查
            order.limit_price = original_limit_price
            self.log.critical(
                "改价结果未知，需人工核对 %s: %s" % (str(order), str(e)),
                **order.log_attributes(),
                method="temp",
            )
            raise orderCannotBeModified(str(e))
        except millsRequestError as e:
            order.limit_price = original_limit_price
            raise orderCannotBeModified(str(e))

        # 新网关返回的 id 是原 tempid（current_id 才是实际委托），旧网关返回新委托的 id，两种都兼容
        order.broker_tempid = trade_with_contract_from_mills['id']
        self.log.debug(
            "Modified limit price, tempid %s current_id %s"
            % (
                trade_with_contract_from_mills['id'],
                trade_with_contract_from_mills.get('current_id'),
            ),
            **order.log_attributes(),
            method="temp",
        )
        broker_order_with_controls.update_order()

        return broker_order_with_controls

    def check_order_can_be_modified_given_control_object_throw_error_if_not(
        self, broker_order_with_controls: millsOrderWithControls
    ):
        try:
            trade_with_contract_from_mills = broker_order_with_controls.get_order_from_broker(
                max_age_seconds=0
            )
        except millsOrderStateUnknown as e:
            raise orderCannotBeModified("Order state unknown: %s" % str(e))

        status = trade_with_contract_from_mills['status']
        if status != MILLS_ORDER_OPEN_STATUS:
            raise orderCannotBeModified(
                "Order can't be modified as status is %s, not %s"
                % (status, MILLS_ORDER_OPEN_STATUS)
            )

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
        for order_with_control in dict_of_orders_with_control.values():
            try:
                order_with_control.update_order_without_alert()
            except millsOrderStateUnknown:
                # 单张委托查不到不影响其他委托；它保留上次已知状态，不会被改成成交 0
                pass

        return dict_of_orders_with_control
