import logging

from syscore.constants import arg_not_supplied
import time

from syslogdiag.log_to_screen import logtoscreen
from sysbrokers.mills.mills_connection_defaults import mills_defaults
from sysobjects.contracts import futuresContract
from sysexecution.orders.base_orders import Order
import json

import requests
import orjson
from websocket import create_connection
from syslogging.logger import *

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
        self._ws_connection = create_connection(url = "ws://"+str(ipaddress)+":"+str(port)+"/websocket")
        pass

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
        res = self.send_ws("/quote","contract_info",futures_contract.as_dict())
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

    def send_get(self,endpoint,params={}):
        url= self._mills_connection_config.get("header")+endpoint;
        session = requests.Session()
        session.auth = (self._mills_connection_config.get("username"), self._mills_connection_config.get("password"))
        req_body = session.get(url=url, params=params).text
        res = orjson.loads(req_body)
        if (res['code'] == 10000):
            return res['data']
        else:
            raise Exception("请求异常", res['msg'])
        return

    def send_post(self, endpoint, params):

        url = self._mills_connection_config.get("header") + endpoint;
        session = requests.Session()
        session.auth = (self._mills_connection_config.get("username"), self._mills_connection_config.get("password"))
        req_body = session.post(url=url,
                     json=orjson.loads(orjson.dumps(params, option=orjson.OPT_SERIALIZE_NUMPY, default=str))).text
        try:
            res = orjson.loads(req_body)
        except Exception as e:
            self.log.error(f"读取返回数据失败:%s,请求地址:%s,请求参数:%s,返回参数:%s",e,endpoint,params,req_body)
        if(res['code'] == 10000):
            return res['data']
        else:
            raise Exception("请求异常", res['msg'])

    def send_ws(self,url,action,data):
        params = {"url": url, "action": action, "data": data}
        # 记录开始时间
        start_time = time.time()
        self._ws_connection.send(json.dumps(json.dumps(params)))
        res = self._ws_connection.recv()
        # 记录结束时间
        end_time = time.time()
        # 计算并打印运行时间
        run_time = end_time - start_time
        logging.debug(f"get data from mills server by {url} {action} for {run_time} seconds.")
        return res

    def query_posistions(self):
        res = self.send_get("/position")
        return res

    def query_min_tick_size(self, contract_object):
        # res = self.send_post("/gateway/query_min_tick_size", contract_object.as_dict())
        res = self.send_post("/quote?action=min_tick", contract_object.as_dict())
        return res

    def place_order(self, new_order: Order):
        res = self.send_post("/order?action=place_order",new_order.as_dict())
        return res

    def query_ask_bid_data(self, contract_object):
        res = self.send_post("/ticks",contract_object.as_dict())
        return res


    def get_order_by_id(self,order):
        res = self.send_post("/order?action=get",order.as_dict())
        return res

    def cancel_order(self, order):
        res = self.send_post("/order?action=cancel",order.as_dict())
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