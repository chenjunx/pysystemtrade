import datetime
from sysbrokers.mills.mills_connection import connectionMills

from sysexecution.order_stacks.broker_order_stack import orderWithControls
from sysexecution.orders.broker_orders import brokerOrder
from sysexecution.tick_data import tickerObject
from collections import namedtuple
from sysexecution.orders.named_order_objects import missing_order,no_parent
from syscore.constants import arg_not_supplied

from sysexecution.trade_qty import tradeQuantity
from sysexecution.orders.broker_orders import brokerOrderType
from copy import copy

def extract_fill_info(order):
    fill_info = [extract_single_fill(order)]
    fill_info_without_bags = [
        single_fill for single_fill in fill_info if single_fill is not None
    ]

    return fill_info_without_bags

import json
from datetime import datetime

def extract_single_fill(single_fill):
    commission = single_fill['fee']
    commission_ccy = single_fill['fee_currency']
    cum_qty = float(single_fill['filled'])
    sign = 1
    if single_fill['side'] == 'sell':
        sign = -1
    signed_qty = cum_qty * sign

    price = single_fill['info']['avgFillPrice'] if single_fill['info']['avgFillPrice'] is None else float(single_fill['info']['avgFillPrice'])
    avg_price = single_fill['info']['avgFillPrice'] if single_fill['info']['avgFillPrice'] is None else float(single_fill['info']['avgFillPrice'])

    time = single_fill['datetime']
    temp_id = single_fill['id']
    client_id = single_fill['clientOrderId']
    contract_month = single_fill['lastTradeDateOrContractMonth']

    singleFill = namedtuple(
        "singleFill",
        [
            "commission",
            "commission_ccy",
            "cum_qty",
            "price",
            "avg_price",
            "time",
            "temp_id",
            "client_id",
            "signed_qty",
            "contract_id",
        ],
    )

    single_fill = singleFill(
        commission,
        commission_ccy,
        cum_qty,
        price,
        avg_price,
        time,
        temp_id,
        client_id,
        signed_qty,
        contract_month,
    )

    return single_fill


def extract_order_info(order):
    account = 1
    perm_id = None
    client_id = 1
    limit_price = order['stopPrice']
    order_sign = 1
    if order['side'] == 'sell':
        order_sign = -1
    order_type = brokerOrderType(order['type'])
    order_id = order['id']
    remain_qty = float(order['info']['remainingSize'])
    total_qty = float(order['amount'])

    orderInfo = namedtuple(
        "orderInfo",
        [
            "account",
            "perm_id",
            "limit_price",
            "order_sign",
            "type",
            "remain_qty",
            "order_object",
            "client_id",
            "order_id",
            "total_qty",
        ],
    )
    order_info = orderInfo(
        account=account,
        perm_id=perm_id,
        limit_price=limit_price,
        order_sign=order_sign,
        type=order_type,
        remain_qty=remain_qty,
        order_object=order,
        client_id=client_id,
        order_id=order_id,
        total_qty=total_qty,
    )

    return order_info



def extract_contract_info(contract, legs=None):
    mills_instrument_code = contract['instrument_code']
    mills_sectype = 'FUT'

    mills_contract_id = [contract['lastTradeDateOrContractMonth']]
    leg_ratios = [1]

    contractInfo = namedtuple(
        "contractInfo",
        [
            "mills_instrument_code",
            "mills_contract_id",
            "mills_sectype",
            "contract_object",
            "legs",
            "leg_ratios",
        ],
    )
    contract_info = contractInfo(
        mills_instrument_code=mills_instrument_code,
        mills_contract_id=mills_contract_id,
        mills_sectype=mills_sectype,
        contract_object=contract,
        legs=legs,
        leg_ratios=leg_ratios,
    )

    return contract_info
class millsBrokerOrder(brokerOrder):
    @classmethod
    def from_broker_trade_object(
        trade_info, extracted_trade_data, instrument_code=arg_not_supplied,strategy_name="",parent=no_parent,side_price=arg_not_supplied,
            mid_price=arg_not_supplied,offside_price=arg_not_supplied
    ):
        sec_type = extracted_trade_data.contract.mills_sectype

        if sec_type not in ["FUT", "BAG"]:
            # Doesn't handle non futures trades, just ignores them
            return missing_order

        if instrument_code is arg_not_supplied:
            instrument_code = extracted_trade_data.contract.mills_instrument_code
        contract_id_list = extracted_trade_data.contract.mills_contract_id

        algo_comment = extracted_trade_data.algo_msg
        order_type = extracted_trade_data.order.type
        limit_price = extracted_trade_data.order.limit_price
        broker_account = extracted_trade_data.order.account
        broker_permid = extracted_trade_data.order.perm_id
        broker_tempid = extracted_trade_data.order.order_id
        broker_clientid = extracted_trade_data.order.client_id

        broker_objects = dict(
            order=extracted_trade_data.order.order_object,
            trade=extracted_trade_data.trade_object,
            contract=extracted_trade_data.contract.contract_object,
        )


        fill = tradeQuantity([extracted_trade_data.fills[0].cum_qty])

        fill_price = extracted_trade_data.fills[0].avg_price
        commission = None
        # todo 手续费查询
        if fill_price is not None:
            commission = float(extracted_trade_data.trade_object['fee'])

        submit_datetime = None
        # if extracted_trade_data.trade_object['datetime'] is not None:
        #     submit_datetime = datetime.strptime(extracted_trade_data.trade_object['datetime'],'%Y-%m-%dT%H:%M:%S.%fZ')
        if 'create_datetime' in extracted_trade_data.trade_object and extracted_trade_data.trade_object['create_datetime'] is not None:
            submit_datetime = datetime.strptime(extracted_trade_data.trade_object['create_datetime'],'%Y-%m-%dT%H:%M:%S.%fZ')
        broker_order = millsBrokerOrder(
            strategy_name,
            instrument_code,
            contract_id_list,
            extracted_trade_data.order.total_qty,
            fill=fill,
            parent=parent,
            order_type=order_type,
            limit_price=limit_price,
            filled_price=fill_price,
            algo_comment=algo_comment,
            # fill_datetime=extracted_trade_data.fills[0].time,
            broker_account=broker_account,
            commission=commission,
            leg_filled_price=extracted_trade_data.fills,
            broker_permid=broker_permid,
            broker_tempid=broker_tempid,
            broker_clientid=broker_clientid,
            submit_datetime=submit_datetime,
            side_price=side_price,
            mid_price=mid_price,
            offside_price=offside_price
        )

        broker_order.broker_objects = broker_objects

        return broker_order

    @property
    def broker_objects(self):
        return getattr(self, "_broker_objects", None)

    @broker_objects.setter
    def broker_objects(self, broker_objects):
        self._broker_objects = broker_objects


class millsOrderCouldntCreateException(Exception):
    pass
class millsOrderWithControls(orderWithControls):
    def __init__(self,order, broker_order: brokerOrder =None,  instrument_code: str = arg_not_supplied, ticker_object: tickerObject = None,connectionMills: connectionMills=None):
        order_info = extract_order_info(order)
        contract_info = extract_contract_info(order)
        fill_info = extract_fill_info(order)
        algo_msg = ""
        active = True
        if order['status'] == 'close':
            active = False

        tradeInfo = namedtuple(
            "tradeInfo",
            ["order", "contract", "fills", "algo_msg", "active", "trade_object"],
        )
        trade_info = tradeInfo(
            order_info, contract_info, fill_info, algo_msg, active, order
        )
        # and stage two
        strategy_name = ''
        parent = no_parent
        side_price = None;
        mid_price = None;
        offside_price = None;

        if broker_order is not None:
            strategy_name = broker_order.key.split("/")[0]
            parent = broker_order.parent
            side_price = broker_order.side_price
            mid_price = broker_order.mid_price
            offside_price = broker_order.offside_price
        mills_broker_order = millsBrokerOrder.from_broker_trade_object(
                trade_info, instrument_code=instrument_code,strategy_name=strategy_name,parent=parent,side_price=side_price,
            mid_price=mid_price,offside_price=offside_price
        )
        if mills_broker_order is missing_order:
            raise millsOrderCouldntCreateException()
        self._connectionMills=connectionMills
        self._orgin_broker_order = broker_order
        super().__init__(broker_order=mills_broker_order, control_object=order, ticker_object=ticker_object)


    def update_order(self):
        trade_with_contract_from_mills = self._connectionMills.get_order_by_id(self.order)
        if trade_with_contract_from_mills is missing_order:
            return missing_order

        ## 检测fill情况,如果已经填充，则更新brokerOrder
        broker_order_from_trade_object = millsOrderWithControls(
            trade_with_contract_from_mills,
            broker_order=self._orgin_broker_order,
            connectionMills=self._connectionMills,
        )


        ##1.判断填充方法  broker_order_from_trade_object.fill.equals_zero()
        new_broker_order = copy(self.order)


        new_broker_order.commission = broker_order_from_trade_object._order.commission
        new_broker_order.broker_tempid = broker_order_from_trade_object._order.broker_tempid
        broker_order_is_filled = not broker_order_from_trade_object.order.fill.equals_zero()
        ## 2.填充方法 new_broker_order.fill_order

        if broker_order_is_filled:
            new_broker_order.fill_order(
                broker_order_from_trade_object.order.fill,
                broker_order_from_trade_object.order.filled_price,
                datetime.strptime(trade_with_contract_from_mills['datetime'],'%Y-%m-%dT%H:%M:%S.%fZ'),
            )

        self._order = new_broker_order

    def broker_limit_price(self) -> float:
        trade_with_contract_from_mills = self._connectionMills.get_order_by_id(self.order)
        if trade_with_contract_from_mills['info']['price'] is None:
            return None
        else:
            return float(trade_with_contract_from_mills['info']['price'])





