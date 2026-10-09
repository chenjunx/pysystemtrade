import logging

from syscore.constants import arg_not_supplied

from syslogdiag.log_to_screen import logtoscreen
from sysbrokers.mills.mills_connection_defaults import mills_defaults
from sysobjects.contracts import futuresContract
from sysexecution.orders.base_orders import Order
import json
import time

import requests
import orjson
from websocket import create_connection
from syslogging.logger import *

# 网关返回这些错误码时，委托的真实状态未知：
#   10004 改价时撤单超时；10005 网关内存里找不到委托；10008 合约配置查询失败
ORDER_STATE_UNKNOWN_CODES = {10004, 10005, 10008}
GET_ORDER_RETRIES = 3
GET_ORDER_RETRY_WAIT_SECONDS = 0.5


class millsRequestError(Exception):
    def __init__(self, msg, code=None, http_status=None):
        super().__init__(msg)
        self.code = code
        self.http_status = http_status


class millsOrderStateUnknown(millsRequestError):
    """
    委托状态未知（10004/10005/10008、网络异常、返回无法解析）
    绝不能当成已撤单或成交 0 处理
    """

    pass


class connectionMills(object):
    def __init__(
            self,
            mills_ipaddress: str = arg_not_supplied,
            mills_port: int = arg_not_supplied,
            account: str = arg_not_supplied,
            log=get_logger("mills-serve"),
    ):
        ipaddress, port,username,password = mills_defaults(mills_ipaddress=mills_ipaddress, mills_port=mills_port)
        self.log = log
        self._mills_connection_config = dict(
            ipaddress=ipaddress, port=port,header="http://"+str(ipaddress)+":"+str(port),username=username,password=password
        )
        self._ws_url = "ws://"+str(ipaddress)+":"+str(port)+"/websocket"
        self._ws_connection = create_connection(url=self._ws_url, timeout=60)
        # broker_tempid -> (查询时间, 返回数据)，用于限制查单频率
        self._order_query_cache = {}

    def on_error(self,error):
        self.log.error(error)

    def on_open(self):
        self.log.info("ws连接成功!")

    def on_close(self):
        self.log.info("ws连接失败!")


    #获取汇率数据
    def query_fx_Data(self):
        res = self.send_get("/api/allforexinfo?base_code=CNY")
        jsonData = orjson.loads(res)
        return jsonData

    #查询期货信息
    def query_contract_info(self,futures_contract: futuresContract):
        # res = self.send_post("/quote?action=contract_info",futures_contract.as_dict())
        endpoint = "/quote"
        action = "contract_info"
        params = futures_contract.as_dict()
        res = self.send_ws(endpoint,action,params)
        return res

    #查询指定的合同的历史价格
    def query_historical_futures_data_for_contract(self, contract_object: futuresContract):
        # res = self.send_post("/gateway/historical_futures_data",contract_object.as_dict())
        # res = self.send_post("/klines?action=day",contract_object.as_dict())
        res = self.send_ws("/klines","day",contract_object.as_dict())
        return res

    # 查询指定的合同的历史价格
    def query_historical_futures_data_for_contract_hour(self, contract_object: futuresContract):
        # res = self.send_post("/gateway/historical_futures_data_hour", contract_object.as_dict())
        # res = self.send_post("/klines?action=hour",contract_object.as_dict())
        res = self.send_ws("/klines","hour",contract_object.as_dict())
        return res

    #查询指定的合同的交易时间段
    def query_trading_hours(self,contract_object: futuresContract):
        # res = self.send_post("/gateway/contract_info_tradingHours",contract_object.as_dict())
        # res = self.send_post("/quote?action=trading_hours",contract_object.as_dict())
        res = self.send_ws("/quote","trading_hours",contract_object.as_dict())
        return res

    #查询账户有多少价值
    def query_total_accout_value(self):
        res = self.send_get("/account?action=total_accout_value")
        return res

    #查询流动资金
    def query_excess_liquidity_value_across(self):
        res = self.send_get("/account?action=excess_liquidity_value_across")
        return res

    def query_active_orders(self):
        # res = self.send_get("/order/query_active_orders")
        res = self.send_get("/order")
        return res

    def send_get(self, endpoint, params=None):
        if params is None:
            params = {}
        url = self._mills_connection_config.get("header") + endpoint
        session = requests.Session()
        session.auth = (self._mills_connection_config.get("username"), self._mills_connection_config.get("password"))
        try:
            response = session.get(url=url, params=params, timeout=10)
            req_body = response.text
        except Exception as e:
            self.log.error(f"请求发送失败: {e}, 地址: {url}, 参数: {params}")
            raise millsRequestError(f"请求发送失败: {e}") from e

        return self._parse_response(response, req_body, url, params)

    def send_post(self, endpoint, params):
        url = self._mills_connection_config.get("header") + endpoint
        session = requests.Session()
        session.auth = (self._mills_connection_config.get("username"), self._mills_connection_config.get("password"))
        try:
            response = session.post(url=url,
                         json=orjson.loads(orjson.dumps(params, option=orjson.OPT_SERIALIZE_NUMPY, default=str)),
                         timeout=10)
            req_body = response.text
        except Exception as e:
            self.log.error(f"请求发送失败: {e}, 地址: {url}, 参数: {params}")
            raise millsRequestError(f"请求发送失败: {e}") from e

        return self._parse_response(response, req_body, url, params)

    def _parse_response(self, response, req_body, url, params):
        try:
            res = orjson.loads(req_body)
        except Exception as e:
            self.log.error(f"解析返回数据失败: {e}, 地址: {url}, 参数: {params}, 返回内容: {req_body}")
            raise millsRequestError(
                f"解析返回数据失败: {e}", http_status=response.status_code
            ) from e

        if (res['code'] == 10000):
            return res['data']
        else:
            self.log.info(f'请求地址:{url},请求参数:{params},返回数据:{req_body}')
            raise millsRequestError(
                "请求异常 code=%s msg=%s" % (res.get('code'), res.get('msg')),
                code=res.get('code'),
                http_status=response.status_code,
            )

    def _order_request(self, action: str, order, retries: int = 1):
        last_error = None
        for attempt in range(retries):
            try:
                return self.send_post("/order?action=%s" % action, order.as_dict())
            except millsRequestError as e:
                if e.code is not None and e.code not in ORDER_STATE_UNKNOWN_CODES:
                    # 网关明确拒绝，委托状态是确定的
                    raise
                last_error = e
                self.log.warning(
                    "委托状态未知 action=%s tempid=%s 第%d次: %s"
                    % (action, order.broker_tempid, attempt + 1, e)
                )
                if attempt < retries - 1:
                    time.sleep(GET_ORDER_RETRY_WAIT_SECONDS)

        raise millsOrderStateUnknown(
            str(last_error), code=last_error.code, http_status=last_error.http_status
        )


    def send_ws(self, url, action, data):
        params = {"url": url, "action": action, "data": data}
        try:
            self._ws_connection.send(json.dumps(json.dumps(params)))
            res = self._ws_connection.recv()
            return res
        except Exception as e:
            self.log.warning("WebSocket请求失败，尝试重连: %s", e)
            try:
                self._ws_connection = create_connection(url=self._ws_url, timeout=60)
                self._ws_connection.send(json.dumps(json.dumps(params)))
                res = self._ws_connection.recv()
                return res
            except Exception as e2:
                self.log.error("WebSocket重连后仍然失败: %s", e2)
                raise

    def query_posistions(self):
        res = self.send_get("/position")
        return res

    def query_min_tick_size(self, contract_object):
        # res = self.send_post("/gateway/query_min_tick_size", contract_object.as_dict())
        res = self.send_post("/quote?action=min_tick", contract_object.as_dict())
        return res

    def place_order(self, new_order: Order):
        # 不重试：超时后单子可能已经下出去了，重发可能重复下单
        self._order_query_cache.pop(new_order.broker_tempid, None)
        res = self._order_request("place_order", new_order, retries=1)
        return res

    def query_ask_bid_data(self, contract_object):
        res = self.send_post("/ticks",contract_object.as_dict())
        return res


    def get_order_by_id(self, order, max_age_seconds: float = 0.0):
        """
        :param max_age_seconds: 同一张委托在这段时间内查过，就直接用上次的结果
        :raises millsOrderStateUnknown: 重试后仍无法确定委托状态
        """
        broker_tempid = order.broker_tempid
        cached = self._order_query_cache.get(broker_tempid, None)
        if (
            max_age_seconds > 0
            and cached is not None
            and time.time() - cached[0] < max_age_seconds
        ):
            return cached[1]

        res = self._order_request("get", order, retries=GET_ORDER_RETRIES)
        self._order_query_cache[broker_tempid] = (time.time(), res)
        return res

    def cancel_order(self, order):
        self._order_query_cache.pop(order.broker_tempid, None)
        res = self._order_request("cancel", order, retries=1)
        return res

    def close_connection(self):
        # self.log.debug("Terminating %s" % str(self._mills_connection_config))
        try:
            #关闭连接
            if self._ws_connection:
                self._ws_connection.close()
        except BaseException:
            self.log.warning(
                "Trying to disconnect mills client failed... ensure process is killed"
            )