import datetime

from sysexecution.order_stacks.broker_order_stack import orderWithControls
from sysexecution.orders.broker_orders import brokerOrder
from sysexecution.tick_data import tickerObject
from collections import namedtuple
from syscore.objects import missing_order, arg_not_supplied, missing_data
from sysexecution.trade_qty import tradeQuantity

def extract_fill_info(order):
    fill_info = [extract_single_fill(order)]
    fill_info_without_bags = [
        single_fill for single_fill in fill_info if single_fill is not None
    ]

    return fill_info_without_bags


def extract_single_fill(single_fill):
    commission = float(single_fill['fee'])
    commission_ccy = single_fill['fee_currency']
    cum_qty = float(single_fill['amount'])
    sign = 1
    if single_fill['side'] == 'sell':
        sign = -1
    signed_qty = cum_qty * sign
    price = float(single_fill['info']['avgFillPrice'])
    avg_price = float(single_fill['info']['avgFillPrice'])

    # move to local time and strip TZ info
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
    account = None
    perm_id = None
    client_id = None
    limit_price = order['stopPrice']
    order_sign = 1
    if order['side'] == 'sell':
        order_sign = -1
    order_type = order['type']
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
        millsBrokerOrder, extracted_trade_data, instrument_code=arg_not_supplied
    ):
        sec_type = extracted_trade_data.contract.mills_sectype

        if sec_type not in ["FUT", "BAG"]:
            # Doesn't handle non futures trades, just ignores them
            return missing_order

        strategy_name = ""
        if instrument_code is arg_not_supplied:
            instrument_code = extracted_trade_data.contract.mills_instrument_code
        contract_id_list = extracted_trade_data.contract.mills_contract_id

        algo_comment = extracted_trade_data.algo_msg
        order_type = extracted_trade_data.order.type
        limit_price = extracted_trade_data.order.limit_price
        broker_account = extracted_trade_data.order.account
        broker_permid = extracted_trade_data.order.perm_id

        broker_objects = dict(
            order=extracted_trade_data.order.order_object,
            trade=extracted_trade_data.trade_object,
            contract=extracted_trade_data.contract.contract_object,
        )


        fill = tradeQuantity(extracted_trade_data.fills[0].cum_qty)

        fill_price = extracted_trade_data.fills[0].avg_price

        broker_order = millsBrokerOrder(
            strategy_name,
            instrument_code,
            contract_id_list,
            extracted_trade_data.order.total_qty,
            fill=fill,
            order_type=order_type,
            limit_price=limit_price,
            filled_price=fill_price,
            algo_comment=algo_comment,
            fill_datetime=extracted_trade_data.order.time,
            broker_account=broker_account,
            commission=extracted_trade_data.order,
            leg_filled_price=extracted_trade_data.fills,
            broker_permid=broker_permid,
            broker_tempid=None,
            broker_clientid=None,
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
    def __init__(self,order, broker_order: brokerOrder =None,  instrument_code: str = None, ticker_object: tickerObject = None):
        order_info = extract_order_info(order)
        contract_info = extract_contract_info(order)
        fill_info = extract_fill_info(order)
        algo_msg = ""
        active = True
        if order['status'] != 'close':
            active = False

        tradeInfo = namedtuple(
            "tradeInfo",
            ["order", "contract", "fills", "algo_msg", "active", "trade_object"],
        )
        trade_info = tradeInfo(
            order_info, contract_info, fill_info, algo_msg, active, order
        )
        # and stage two
        mills_broker_order = millsBrokerOrder.from_broker_trade_object(
            trade_info, instrument_code=instrument_code
        )

        # this can go wrong eg for FX
        if mills_broker_order is missing_order:
            raise millsOrderCouldntCreateException()
        # if broker_order is None:
        #     ## trade_with_contract_from_mills转换成broker order
        #     # broker_order = create_broker_order_from_trade_with_contract(
        #     #     trade_with_contract_from_mills, instrument_code
        #     # )
        #     active = False
        #     if order['status'] != 'close':
        #         active = True
        #     order_type = brokerOrderType('limit')
        #     if order['type'] == 'market':
        #         order_type =  brokerOrderType('market')
        #     fill = tradeQuantity([])
        #     if order['symbol'].startswith("BTC"):
        #         fill = tradeQuantity([int(float(order['filled'])/0.01),int(float(order['amount'])/0.01)])
        #     if order['symbol'].startswith("ETH"):
        #         fill = tradeQuantity([int(float(order['filled'])/0.1),int(float(order['amount'])/0.1)])
        #     broker_order = brokerOrder(
        #                             fill=fill,
        #                              fill_datetime=order['datetime'],
        #                               key= order['id'],
        #                               order_id=order['id'],
        #                               filled_price=order['info']['avgFillPrice'],
        #                               trade=order['amount'],
        #                                commission=order['fee'],
        #                                 active = active,
        #                                 order_type = order_type,
        #                                 manual_fill=True)

        super().__init__(millsBrokerOrder, control_object=order, ticker_object=ticker_object)

    @property
    def ticker(self) -> tickerObject:
        return super().ticker()

    def add_or_replace_ticker(self, new_ticker: tickerObject):
        super().add_or_replace_ticker(new_ticker)

    def set_submit_datetime(self, new_submit_datetime: datetime.datetime):
        super().set_submit_datetime(new_submit_datetime)

    @property
    def control_object(self):
        return super().control_object()

    def replace_control_object(self, new_control_object):
        super().replace_control_object(new_control_object)

    @property
    def order(self) -> brokerOrder:
        return super().order()

    @property
    def datetime_order_submitted(self):
        return super().datetime_order_submitted()

    def message_required(self, messaging_frequency_seconds: int = 30) -> bool:
        return super().message_required(messaging_frequency_seconds)

    def seconds_since_last_message(self) -> float:
        return super().seconds_since_last_message()

    @property
    def last_message_time(self):
        return super().last_message_time()

    def reset_last_message_time(self):
        super().reset_last_message_time()

    def seconds_since_submission(self) -> float:
        return super().seconds_since_submission()

    def update_order(self):
        pass

    @property
    def current_limit_price(self) -> float:
        return super().current_limit_price()

    def completed(self) -> bool:
        return super().completed()

    def broker_limit_price(self) -> float:
        pass