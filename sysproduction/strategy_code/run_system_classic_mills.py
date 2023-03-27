"""
this:

- gets capital from the database (earmarked with a strategy name)
- runs a backtest using that capital level, and mongodb data
- gets the final positions and position buffers
- writes these into a table (earmarked with a strategy name)


"""

from syscore.constants import missing_data, arg_not_supplied

from sysdata.config.configdata import Config
from sysdata.data_blob import dataBlob

from sysobjects.production.optimal_positions import bufferedOptimalPositions
from sysobjects.production.tradeable_object import instrumentStrategy

from sysproduction.data.currency_data import dataCurrency
from sysproduction.data.capital import dataCapital
from sysproduction.data.contracts import dataContracts
from sysproduction.data.positions import dataOptimalPositions
from sysproduction.data.sim_data import get_sim_data_object_for_production

from sysproduction.data.backtest import store_backtest_state

from syslogdiag.log_to_screen import logtoscreen

# from systems.provided.futures_chapter15.basesystem import futures_system
from systems.basesystem import System


class runSystemClassic(object):
    def __init__(
        self,
        data: dataBlob,
        strategy_name: str,
        backtest_config_filename=arg_not_supplied,
    ):

        if backtest_config_filename is arg_not_supplied:
            raise Exception("Need to supply config filename")

        self.data = data
        self.strategy_name = strategy_name
        self.backtest_config_filename = backtest_config_filename

    ## DO NOT CHANGE THE NAME OF THIS FUNCTION
    def run_backtest(self):
        strategy_name = self.strategy_name
        data = self.data

        base_currency, notional_trading_capital = self._get_currency_and_capital()

        system = self.system_method(
            notional_trading_capital=notional_trading_capital,
            base_currency=base_currency,
        )

        function_to_call_on_update = self.function_to_call_on_update
        function_to_call_on_update(
            data=data, strategy_name=strategy_name, system=system
        )

        store_backtest_state(data, system, strategy_name=strategy_name)

    ## MODIFY THIS WHEN INHERITING FOR A DIFFERENT STRATEGY
    ## ARGUMENTS MUST BE: data: dataBlob, strategy_name: str, system: System
    @property
    def function_to_call_on_update(self):
        return updated_buffered_positions

    def _get_currency_and_capital(self):
        data = self.data
        strategy_name = self.strategy_name

        capital_data = dataCapital(data)
        notional_trading_capital = capital_data.get_current_capital_for_strategy(
            strategy_name
        )
        if notional_trading_capital is missing_data:
            # critical log will send email
            error_msg = (
                "Capital data is missing for %s: can't run backtest" % strategy_name
            )
            data.log.critical(error_msg)
            raise Exception(error_msg)

        currency_data = dataCurrency(data)
        base_currency = currency_data.get_base_currency()

        self.data.log.msg(
            "Using capital of %s %.2f" % (base_currency, notional_trading_capital)
        )

        return base_currency, notional_trading_capital

    # DO NOT CHANGE THE NAME OF THIS FUNCTION; IT IS HARDCODED INTO CONFIGURATION FILES
    # BECAUSE IT IS ALSO USED TO LOAD BACKTESTS
    def system_method(
        self,
        notional_trading_capital: float = arg_not_supplied,
        base_currency: str = arg_not_supplied,
    ) -> System:
        data = self.data
        backtest_config_filename = self.backtest_config_filename

        system = production_classic_futures_system(
            data,
            backtest_config_filename,
            log=data.log,
            notional_trading_capital=notional_trading_capital,
            base_currency=base_currency,
        )

        return system


def production_classic_futures_system(
    data: dataBlob,
    config_filename: str,
    log=logtoscreen("futures_system"),
    notional_trading_capital: float = arg_not_supplied,
    base_currency: str = arg_not_supplied,
) -> System:

    log_level = "on"

    sim_data = get_sim_data_object_for_production(data)
    config = Config(config_filename)

    # Overwrite capital and base currency
    if notional_trading_capital is not arg_not_supplied:
        config.notional_trading_capital = notional_trading_capital

    if base_currency is not arg_not_supplied:
        config.base_currency = base_currency

    system = futures_system(data=sim_data, config=config)
    system._log = log

    system.set_logging_level(log_level)

    return system


def updated_buffered_positions(data: dataBlob, strategy_name: str, system: System):
    log = data.log

    data_optimal_positions = dataOptimalPositions(data)

    list_of_instruments = system.get_instrument_list()
    for instrument_code in list_of_instruments:
        lower_buffer, upper_buffer = get_position_buffers_from_system(
            system, instrument_code
        )
        position_entry = construct_position_entry(
            data=data,
            system=system,
            instrument_code=instrument_code,
            lower_buffer=lower_buffer,
            upper_buffer=upper_buffer,
        )
        instrument_strategy = instrumentStrategy(
            instrument_code=instrument_code, strategy_name=strategy_name
        )
        data_optimal_positions.update_optimal_position_for_instrument_strategy(
            instrument_strategy=instrument_strategy, position_entry=position_entry
        )
        log.msg(
            "New buffered positions %.3f %.3f"
            % (position_entry.lower_position, position_entry.upper_position),
            instrument_code=instrument_code,
        )


def get_position_buffers_from_system(system: System, instrument_code: str):
    buffers = system.portfolio.get_buffers_for_position(
        instrument_code
    )  # get the upper and lower edges of the buffer
    lower_buffer = buffers.iloc[-1].bot_pos
    upper_buffer = buffers.iloc[-1].top_pos

    return lower_buffer, upper_buffer


def construct_position_entry(
    data: dataBlob,
    system: System,
    instrument_code: str,
    lower_buffer: float,
    upper_buffer: float,
) -> bufferedOptimalPositions:

    diag_contracts = dataContracts(data)
    reference_price = system.rawdata.get_daily_prices(instrument_code).iloc[-1]
    reference_contract = diag_contracts.get_priced_contract_id(instrument_code)
    position_entry = bufferedOptimalPositions(
        lower_buffer, upper_buffer, reference_price, reference_contract
    )

    return position_entry


from systems.forecasting import Rules
from systems.forecast_combine import ForecastCombine
from systems.forecast_scale_cap import ForecastScaleCap
# from systems.rawdata import RawData
from systems.positionsizing import PositionSizing
from systems.portfolio import Portfolios
from systems.accounts.accounts_stage import Account
from sysdata.sim.csv_futures_sim_data import csvFuturesSimData
from systems.provided.rob_system.rawdata import myFuturesRawData
def futures_system(
    data=arg_not_supplied,
    config=arg_not_supplied,
    trading_rules=arg_not_supplied,
    log_level="on",
):
    """

    :param data: data object (defaults to reading from csv files)
    :type data: sysdata.data.simData, or anything that inherits from it

    :param config: Configuration object (defaults to futuresconfig.yaml in this directory)
    :type config: sysdata.configdata.Config

    :param trading_rules: Set of trading rules to use (defaults to set specified in config object)
    :type trading_rules: list or dict of TradingRules, or something that can be parsed to that

    :param log_level: How much logging to do
    :type log_level: str


    >>> system=futures_system(log_level="off")
    >>> system
    System with stages: accounts, portfolio, positionSize, rawdata, combForecast, forecastScaleCap, rules
    >>> system.rules.get_raw_forecast("EDOLLAR", "ewmac2_8").dropna().head(2)
                ewmac2_8
    1983-10-10  0.695929
    1983-10-11 -0.604704

                ewmac2_8
    2015-04-21  0.172416
    2015-04-22 -0.477559
    >>> system.rules.get_raw_forecast("EDOLLAR", "carry").dropna().head(2)
                   carry
    1983-10-10  0.952297
    1983-10-11  0.854075

                   carry
    2015-04-21  0.350892
    2015-04-22  0.350892
    """

    if data is arg_not_supplied:
        data = csvFuturesSimData()

    if config is arg_not_supplied:
        config = Config("systems.provided.futures_chapter15.futuresconfig.yaml")

    rules = Rules(trading_rules)

    system = System(
        [
            Account(),
            Portfolios(),
            PositionSizing(),
            myFuturesRawData(),
            ForecastCombine(),
            ForecastScaleCap(),
            rules,
        ],
        data,
        config,
    )

    system.set_logging_level(log_level)

    return system