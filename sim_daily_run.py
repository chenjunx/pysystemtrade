# import pydevd_pycharm
# pydevd_pycharm.settrace('192.168.50.43', port=12345, stdoutToServer=True,
#                         stderrToServer=True)
from systems.basesystem import System
from systems.risk import Risk
from systems.provided.dynamic_small_system_optimise.accounts_stage import (
    accountForOptimisedStage,
)
from systems.provided.dynamic_small_system_optimise.optimised_positions_stage import (
    optimisedPositions,
)
from systems.portfolio import Portfolios
from systems.positionsizing import PositionSizing
from systems.provided.rob_system.rawdata import myFuturesRawData
from systems.forecast_combine import ForecastCombine
from systems.forecasting import Rules
from sysdata.sim.db_futures_sim_data import dbFuturesSimData
from sysdata.config.configdata import Config
from systems.provided.attenuate_vol.vol_attenuation_forecast_scale_cap import (
    volAttenForecastScaleCap,
)
import akshare as ak

data = dbFuturesSimData()

my_system = System(stage_list=[Risk(),
            accountForOptimisedStage(),
            optimisedPositions(),
            Portfolios(),
            PositionSizing(),
            myFuturesRawData(),
            ForecastCombine(),
            volAttenForecastScaleCap(),
            Rules()],
                data=data,
                config=Config("/home/xiachenjun/pysystemtrade/systems/provided/mills/mills_future_estimate_single.yaml")
               )

# my_system.config.use_instrument_weight_estimates = True
#动态系统
# my_system.accounts.optimised_portfolio().percent.curve().to_csv("/home/xiachenjun/sim_dynamic.csv")
#静态系统
# my_system.accounts.portfolio().percent.curve().to_csv("/home/xiachenjun/sim.csv")
import datetime
from arctic import Arctic
store = Arctic('localhost')
store.initialize_library('daily_monitor_data')

library = store['daily_monitor_data']
library.write('sim', my_system.accounts.portfolio().percent.curve())
library.write('sim_dynamic', my_system.accounts.optimised_portfolio().percent.curve())
current_date = datetime.datetime.today().date()
library.write('sim_pct_change'+'/'+current_date.strftime("%Y%m%d"), my_system.portfolio.returns_pre_processor().get_net_returns())
library.write('sim_pct_change_corr'+'/'+current_date.strftime("%Y%m%d"), my_system.portfolio.returns_pre_processor().get_net_returns().corr())
library.write('sim_instrument_weights'+'/'+current_date.strftime("%Y%m%d"), my_system.portfolio.get_instrument_weights())
library.write('zzsp_index', ak.futures_index_ccidx(symbol="中证商品期货指数"))