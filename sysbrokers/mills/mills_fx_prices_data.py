from syslogdiag.log_to_screen import logtoscreen

from sysbrokers.broker_fx_prices_data import brokerFxPricesData
from sysobjects.spot_fx_prices import fxPrices
from collections import namedtuple
from syscore.fileutils import get_filename_for_package
from syscore.objects import missing_instrument, missing_file, missing_data
import pandas as pd
from sysbrokers.mills.mills_connection import connectionMills
from datetime import datetime
from syscore.pdutils import  DEFAULT_DATE_FORMAT


Mills_CCY_CONFIG_FILE = get_filename_for_package("sysbrokers.mills.mills_config_spot_FX.csv")

millsFXConfig = namedtuple("ibFXConfig", ["ccy1", "ccy2", "invert"])

class millsFxPricesData(brokerFxPricesData):
    def __init__(self, millsconnection: connectionMills, log=logtoscreen("millsFxPricesData")):
        self._millsconnection = millsconnection
        super().__init__(log=log)

    #从配置中读取外汇配置
    def get_list_of_fxcodes(self) -> list:
        config_data = self._get_mills_fx_config()
        if config_data is missing_file:
            self.log.warn("Can't get list of fxcodes for mills as config file missing")
            return []
        list_of_codes = list(config_data.CODE)
        return list_of_codes

    #获取外部汇率的方法(目前支持人民币对美元)
    def _get_fx_prices_without_checking(self, currency_code: str) -> fxPrices:
        if currency_code == 'CNHUSD':
            jsonData = self._millsconnection.query_fx_Data()
            # fx_data = pd.Series( [jsonData['conversion_rates']['USD']],index=[datetime.strptime('2022-03-05 00:00:00',DEFAULT_DATE_FORMAT)])
            now = datetime.strptime(datetime.now().strftime('%Y-%m-%d') + ' 23:00:00', '%Y-%m-%d %H:%M:%S')
            fx_data = pd.Series( [jsonData['conversion_rates']['USD']],index=[now])
            fx_data = fxPrices(fx_data.sort_index())
            return fx_data

    def update_fx_prices(self, *args, **kwargs):

        pass

    def add_fx_prices(self, *args, **kwargs):
        pass

    def _delete_fx_prices_without_any_warning_be_careful(self, *args, **kwargs):
        pass

    def _add_fx_prices_without_checking_for_existing_entry(self, *args, **kwargs):
        pass

# Configuration read in and cache
    def _get_mills_fx_config(self) -> pd.DataFrame:
        config = getattr(self, "_config", None)
        if config is None:
            config = self._get_and_set_mills_config_from_file()

        return config


    def _get_and_set_mills_config_from_file(self) -> pd.DataFrame:

        try:
            config_data = pd.read_csv(Mills_CCY_CONFIG_FILE)
        except BaseException:
            self.log.warn("Can't read file %s" % Mills_CCY_CONFIG_FILE)
            config_data = missing_file

        self._config = config_data

        return config_data