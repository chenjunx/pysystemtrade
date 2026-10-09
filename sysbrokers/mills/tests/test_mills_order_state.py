"""
mills 网关委托状态处理的测试，网关请求全部用脚本化的假返回代替，不会连接网关
"""
import pytest

from syscore.exceptions import orderCannotBeModified
from syslogging.logger import get_logger
from sysexecution.orders.broker_orders import brokerOrder, limit_order_type

import sysbrokers.mills.mills_connection as mills_connection_module
from sysbrokers.mills.mills_connection import (
    connectionMills,
    millsOrderStateUnknown,
    millsRequestError,
)
from sysbrokers.mills.mills_execution_stack import millsExecutionStackData
from sysbrokers.mills.mills_order_with_controls import (
    millsOrderWithControls,
    extract_single_fill,
)
from sysexecution.orders.named_order_objects import missing_order

ORIGINAL_TEMPID = "72ffee9c3ffbb49c383da6b536ca51d7"
NEW_TEMPID = "513b3c4a098b0cdd6787b56d600a0aed"


def raw_order(
    tempid=ORIGINAL_TEMPID,
    filled=0.0,
    status="open",
    limit_price=3079.0,
    avg_fill_price=None,
    fee=0.0,
    **extra_fields,
):
    order = dict(
        id=tempid,
        filled=filled,
        status=status,
        side="sell",
        amount=-1.0,
        type="limit",
        stopPrice=limit_price,
        fee=fee,
        fee_currency="CNY",
        datetime="2026-10-09T01:25:53.000Z",
        clientOrderId="",
        lastTradeDateOrContractMonth="20270100",
        instrument_code="RB",
        info=dict(
            avgFillPrice=avg_fill_price,
            remainingSize=1.0 - abs(filled),
            price=limit_price,
        ),
    )
    order.update(extra_fields)
    return order


def gateway_error(code, msg="错误"):
    return millsRequestError("请求异常 code=%s msg=%s" % (code, msg), code=code, http_status=400)


class scriptedConnection(connectionMills):
    """按 action 依次返回脚本里的结果；结果是异常时抛出"""

    def __init__(self, **scripts):
        self.log = get_logger("test-mills")
        self._order_query_cache = {}
        self._scripts = {action: list(results) for action, results in scripts.items()}
        self.calls = []

    def send_post(self, endpoint, params):
        action = endpoint.split("action=")[1]
        self.calls.append((action, params.get("broker_tempid")))
        result = self._scripts[action].pop(0)
        if isinstance(result, Exception):
            raise result
        return result

    def number_of_calls(self, action):
        return len([call for call in self.calls if call[0] == action])


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(mills_connection_module.time, "sleep", lambda seconds: None)


def db_broker_order(broker_tempid=ORIGINAL_TEMPID, fill=0, limit_price=3079.0):
    return brokerOrder(
        "mills_future",
        "RB",
        "20270100",
        [-1],
        fill=[fill],
        order_type=limit_order_type,
        limit_price=limit_price,
        broker_tempid=broker_tempid,
        parent=5005,
        order_id=5114,
    )


def execution_stack(connection):
    stack = millsExecutionStackData.__new__(millsExecutionStackData)
    stack._connection_Mills = connection
    stack.log = get_logger("test-mills-stack")
    return stack


def placed_order_with_controls(connection):
    # 和 put_order_on_stack 一样，用下单回包创建
    return millsOrderWithControls(
        raw_order(),
        broker_order=db_broker_order(),
        connectionMills=connection,
    )


# 错误码处理


def test_10005_is_state_unknown_after_retries_and_fill_unchanged():
    connection = scriptedConnection(get=[gateway_error(10005, "该委托单不存在")] * 3)
    order_with_controls = placed_order_with_controls(connection)

    with pytest.raises(millsOrderStateUnknown):
        order_with_controls.update_order()

    assert connection.number_of_calls("get") == 3
    assert order_with_controls.order.fill.equals_zero()


@pytest.mark.parametrize("code", [10004, 10005, 10008])
def test_unknown_codes_raise_state_unknown(code):
    connection = scriptedConnection(get=[gateway_error(code)] * 3)

    with pytest.raises(millsOrderStateUnknown):
        connection.get_order_by_id(db_broker_order())


def test_network_error_is_state_unknown():
    connection = scriptedConnection(get=[millsRequestError("请求发送失败: timeout")] * 3)

    with pytest.raises(millsOrderStateUnknown):
        connection.get_order_by_id(db_broker_order())


def test_other_business_error_is_not_retried_and_not_unknown():
    connection = scriptedConnection(get=[gateway_error(10001, "参数错误")])

    with pytest.raises(millsRequestError) as error:
        connection.get_order_by_id(db_broker_order())

    assert not isinstance(error.value, millsOrderStateUnknown)
    assert connection.number_of_calls("get") == 1


def test_transient_10005_then_fill_is_applied():
    connection = scriptedConnection(
        get=[
            gateway_error(10005, "该委托单不存在"),
            raw_order(filled=-1.0, status="close", avg_fill_price=3068.0, fee=7.5),
        ]
    )
    order_with_controls = placed_order_with_controls(connection)

    order_with_controls.update_order()

    assert list(order_with_controls.order.fill) == [-1]
    assert order_with_controls.order.filled_price == 3068.0
    assert order_with_controls.order.commission == 7.5


def test_place_order_is_not_retried_when_result_unknown():
    connection = scriptedConnection(place_order=[millsRequestError("请求发送失败: timeout")])

    with pytest.raises(millsOrderStateUnknown):
        connection.place_order(db_broker_order(broker_tempid=""))

    assert connection.number_of_calls("place_order") == 1


# 撤单判断


def test_end_of_day_cancel_check_treats_unknown_as_not_cancelled():
    connection = scriptedConnection(get=[gateway_error(10005, "该委托单不存在")] * 3)
    stack = execution_stack(connection)

    assert stack.check_order_is_cancelled(db_broker_order()) is False


@pytest.mark.parametrize(
    "status, filled, expected",
    [
        ("close", 0.0, True),
        ("close", -1.0, False),
        ("open", 0.0, False),
    ],
)
def test_cancel_check_given_control_object(status, filled, expected):
    connection = scriptedConnection(get=[raw_order(status=status, filled=filled)])
    stack = execution_stack(connection)

    assert (
        stack.check_order_is_cancelled_given_control_object(
            placed_order_with_controls(connection)
        )
        is expected
    )


def test_cancel_check_given_control_object_raises_when_unknown():
    connection = scriptedConnection(get=[gateway_error(10008)] * 3)
    stack = execution_stack(connection)

    with pytest.raises(millsOrderStateUnknown):
        stack.check_order_is_cancelled_given_control_object(
            placed_order_with_controls(connection)
        )


# 成交匹配


def test_storage_refresh_keeps_last_state_for_unknown_order():
    connection = scriptedConnection()
    stack = execution_stack(connection)
    unknown_order = placed_order_with_controls(connection)
    filled_order = millsOrderWithControls(
        raw_order(tempid="other"),
        broker_order=db_broker_order(broker_tempid="other"),
        connectionMills=connection,
    )
    stack._traded_object_store = {
        ORIGINAL_TEMPID: unknown_order,
        "other": filled_order,
    }
    connection._scripts["get"] = [gateway_error(10005)] * 3 + [
        raw_order(tempid="other", filled=-1.0, status="close", avg_fill_price=3068.0)
    ]

    stack._get_dict_of_control_orders_from_storage()

    assert unknown_order.order.fill.equals_zero()
    assert list(filled_order.order.fill) == [-1]


def test_match_after_restart_finds_closed_filled_order():
    connection = scriptedConnection(
        get=[raw_order(filled=-1.0, status="close", avg_fill_price=3068.0, fee=7.5)]
    )
    stack = execution_stack(connection)
    stack._traded_object_store = {}

    matched_order = stack.match_db_broker_order_to_order_from_brokers(db_broker_order())

    assert list(matched_order.fill) == [-1]
    assert list(matched_order.trade) == [-1]
    assert matched_order.filled_price == 3068.0
    assert matched_order.parent == 5005


def test_match_after_restart_returns_missing_when_unknown():
    connection = scriptedConnection(get=[gateway_error(10005)] * 3)
    stack = execution_stack(connection)
    stack._traded_object_store = {}

    assert stack.match_db_broker_order_to_order_from_brokers(db_broker_order()) is missing_order


def test_leg_filled_price_is_refreshed():
    connection = scriptedConnection(
        get=[raw_order(tempid=NEW_TEMPID, filled=-1.0, status="close", avg_fill_price=3077.0)]
    )
    order_with_controls = placed_order_with_controls(connection)

    order_with_controls.update_order()

    [single_fill] = order_with_controls.order.leg_filled_price
    assert single_fill.temp_id == NEW_TEMPID
    assert single_fill.cum_qty == -1.0


def test_signed_qty_keeps_gateway_sign():
    single_fill = extract_single_fill(raw_order(filled=-1.0, avg_fill_price=3068.0))

    assert single_fill.signed_qty == -1.0


# 改价


def test_modify_with_new_gateway_keeps_original_tempid_and_ignores_current_id():
    connection = scriptedConnection(
        get=[
            raw_order(status="open"),
            raw_order(filled=-1.0, status="close", limit_price=3077.0, avg_fill_price=3077.0),
        ],
        place_order=[
            raw_order(limit_price=3077.0, current_id=NEW_TEMPID),
        ],
    )
    stack = execution_stack(connection)

    order_with_controls = stack.modify_limit_price_given_control_object(
        placed_order_with_controls(connection), 3077.0
    )

    assert order_with_controls.order.broker_tempid == ORIGINAL_TEMPID
    assert order_with_controls.order.limit_price == 3077.0
    assert list(order_with_controls.order.fill) == [-1]


def test_modify_with_old_gateway_uses_new_tempid():
    connection = scriptedConnection(
        get=[raw_order(status="open"), raw_order(tempid=NEW_TEMPID, limit_price=3077.0)],
        place_order=[raw_order(tempid=NEW_TEMPID, limit_price=3077.0)],
    )
    stack = execution_stack(connection)

    order_with_controls = stack.modify_limit_price_given_control_object(
        placed_order_with_controls(connection), 3077.0
    )

    assert order_with_controls.order.broker_tempid == NEW_TEMPID


def test_modify_10004_restores_limit_price_and_raises_cannot_be_modified():
    connection = scriptedConnection(
        get=[raw_order(status="open")],
        place_order=[gateway_error(10004, "撤单超时")],
    )
    stack = execution_stack(connection)
    order_with_controls = placed_order_with_controls(connection)

    with pytest.raises(orderCannotBeModified):
        stack.modify_limit_price_given_control_object(order_with_controls, 3077.0)

    assert order_with_controls.order.limit_price == 3079.0
    assert order_with_controls.order.broker_tempid == ORIGINAL_TEMPID


def test_modify_closed_order_raises_cannot_be_modified():
    connection = scriptedConnection(get=[raw_order(status="close", filled=-1.0)])
    stack = execution_stack(connection)

    with pytest.raises(orderCannotBeModified):
        stack.modify_limit_price_given_control_object(
            placed_order_with_controls(connection), 3077.0
        )

    assert connection.number_of_calls("place_order") == 0


# 查单频率


def test_queries_are_throttled_and_cancel_clears_cache():
    connection = scriptedConnection(
        get=[raw_order(), raw_order(status="close")],
        cancel=[{}],
    )
    order_with_controls = placed_order_with_controls(connection)

    order_with_controls.update_order()
    order_with_controls.update_order()
    assert connection.number_of_calls("get") == 1

    connection.cancel_order(order_with_controls.order)
    order_with_controls.update_order()
    assert connection.number_of_calls("get") == 2
