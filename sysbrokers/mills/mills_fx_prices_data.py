from collections import namedtuple
import pandas as pd

from sysbrokers.broker_fx_prices_data import brokerFxPricesData
from sysbrokers.mills.client.mills_fx_client  import millsFxClient

from sysobjects.spot_fx_prices import fxPrices
from syslogdiag.log_to_screen import logtoscreen
from syscore.fileutils import get_filename_for_package
from syscore.objects import missing_instrument, missing_file, missing_data

MILLS_CCY_CONFIG_FILE = get_filename_for_package("sysbrokers.mills.mills_config_spot_FX.csv")

millsFXConfig = namedtuple("millsFXConfig", ["ccy1", "ccy2", "invert"])


class millsFxPricesData(brokerFxPricesData):
    def __init__(self,millsconnection, log=logtoscreen("millsFxPricesData")):
        self._millsconnection= millsconnection
        super().__init__(log=log)

    def __repr__(self):
        return "mills FX price data"

    @property
    def millsconnection(self):
        return self._millsconnection

    @property
    def mills_client(self) -> millsFxClient:
        client = getattr(self, "_mills_client", None)
        if client is None:
            client = self._mills_client = millsFxClient(
                millsconnection=self._millsconnection, log=self.log
            )

        return client

    def get_list_of_fxcodes(self) -> list:
        config_data = self._get_mills_fx_config()
        if config_data is missing_file:
            self.log.warn("Can't get list of fxcodes for mills as config file missing")
            return []
        list_of_codes = list(config_data.CODE)

        return list_of_codes

    def _get_fx_prices_without_checking(self, currency_code: str) -> fxPrices:
        mills_config_for_code = self._get_config_info_for_code(currency_code)
        if mills_config_for_code is missing_instrument:
            self.log.warn(
                "Can't get prices as missing mills config for %s" % currency_code,
                fx_code=currency_code,
            )
            return fxPrices.create_empty()

        data = self._get_fx_prices_with_mills_config(currency_code, mills_config_for_code)

        return data

    def _get_fx_prices_with_mills_config(
        self, currency_code: str, mills_config_for_code: millsFXConfig
    ) -> fxPrices:
        raw_fx_prices_as_series = self._get_raw_fx_prices(mills_config_for_code)

        if len(raw_fx_prices_as_series) == 0:
            self.log.warn(
                "No available mills prices for %s %s"
                % (currency_code, str(mills_config_for_code)),
                fx_code=currency_code,
            )
            return fxPrices.create_empty()

        if mills_config_for_code.invert:
            raw_fx_prices = 1.0 / raw_fx_prices_as_series
        else:
            raw_fx_prices = raw_fx_prices_as_series

        # turn into a fxPrices
        fx_prices = fxPrices(raw_fx_prices)

        self.log.msg("Downloaded %d prices" % len(fx_prices), fx_code=currency_code)

        return fx_prices

    def _get_raw_fx_prices(self, mills_config_for_code: millsFXConfig) -> pd.Series:
        ccy1 = mills_config_for_code.ccy1
        ccy2 = mills_config_for_code.ccy2
        raw_fx_prices = self._mills_clinet.broker_get_daily_fx_data(ccy1, ccy2)
        if raw_fx_prices is missing_data:
            return pd.Series()
        raw_fx_prices_as_series = raw_fx_prices["FINAL"]

        return raw_fx_prices_as_series

    def _get_config_info_for_code(self, currency_code: str) -> millsFXConfig:
        new_log = self.log.setup(currency_code=currency_code)

        config_data = self._get_mills_fx_config()
        if config_data is missing_file:
            new_log.warn(
                "Can't get mills FX config for %s as config file missing" % currency_code,
                fx_code=currency_code,
            )

            return missing_instrument

        ccy1 = config_data[config_data.CODE == currency_code].CCY1.values[0]
        ccy2 = config_data[config_data.CODE == currency_code].CCY2.values[0]
        invert = (
            config_data[config_data.CODE == currency_code].INVERT.values[0] == "YES"
        )

        ib_config_for_code = millsFXConfig(ccy1, ccy2, invert)

        return ib_config_for_code

    # Configuration read in and cache
    def _get_mills_fx_config(self) -> pd.DataFrame:
        config = getattr(self, "_config", None)
        if config is None:
            config = self._get_and_set_mills_config_from_file()

        return config

    def _get_and_set_mills_config_from_file(self) -> pd.DataFrame:

        try:
            config_data = pd.read_csv(MILLS_CCY_CONFIG_FILE)
        except BaseException:
            self.log.warn("Can't read file %s" % MILLS_CCY_CONFIG_FILE)
            config_data = missing_file

        self._config = config_data

        return config_data
