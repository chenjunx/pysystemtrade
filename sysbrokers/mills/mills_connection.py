from syscore.objects import missing_data, arg_not_supplied,missing_contract

from syslogdiag.log_to_screen import logtoscreen
from sysbrokers.mills.mills_connection_defaults import  mills_defaults
from sysobjects.contracts import futuresContract

import requests
import json
import pandas as pd
class connectionMills(object):
    def __init__(
            self,
            mills_ipaddress: str = arg_not_supplied,
            mills_port: int = arg_not_supplied,
            account: str = arg_not_supplied,
            log=logtoscreen("connectionMills"),
    ):
        ipaddress, port = mills_defaults(mills_ipaddress=mills_ipaddress, mills_port=mills_port)

        log.label(broker="mills")
        self._mills_connection_config = dict(
            ipaddress=ipaddress, port=port,header="http://"+str(ipaddress)+":"+str(port)
        )
        pass

    @property
    def log(self):
        return self._log

    #获取汇率数据
    def query_fx_Data(self):
        url = "https://v6.exchangerate-api.com/v6/25c26574f2eac4a80b0def3c/latest/CNY"
        res = requests.get(url)
        print(res.text)
        jsonData = json.loads(res.text)
        return jsonData

    #查询期货信息
    def query_contract_info(self,futures_contract: futuresContract):
        res = self.send_post("/gateway/contract_info",futures_contract.as_dict())
        return res

    #查询指定的合同的历史价格
    def query_historical_futures_data_for_contract(self, contract_object: futuresContract):
        res = self.send_post("/gateway/historical_futures_data",contract_object.as_dict())
        return res

    # 查询指定的合同的历史价格
    def query_historical_futures_data_for_contract_hour(self, contract_object: futuresContract):
        res = self.send_post("/gateway/historical_futures_data_hour", contract_object.as_dict())
        return res

    #查询指定的合同的交易时间段
    def query_trading_hours(self,contract_object: futuresContract):
        res = self.send_post("/gateway/contract_info_tradingHours",contract_object.as_dict())
        return res

    #查询账户有多少价值
    def query_total_accout_value(self):
        res = self.send_get("/gateway/total_accout_value")
        return res

    #查询流动资金
    def query_excess_liquidity_value_across(self):
        res = self.send_get("/gateway/excess_liquidity_value_across")
        return res

    def query_active_orders(self):
        res = self.send_get("/gateway/query_active_orders")
        return res

    def send_get(self,endpoint,params={}):
        url= self._mills_connection_config.get("header")+endpoint;
        return requests.get(url=url,params=params).text

    def send_post(self, endpoint, params):
        url = self._mills_connection_config.get("header") + endpoint;
        return requests.post(url=url, json=json.dumps(params)).text
