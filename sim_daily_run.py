# import pydevd_pycharm
# pydevd_pycharm.settrace('localhost', port=12345, stdoutToServer=True,
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
from systems.forecast_scale_cap import ForecastScaleCap
from sysdata.sim.db_futures_sim_data import dbFuturesSimData
from sysdata.config.configdata import Config
from systems.provided.attenuate_vol.vol_attenuation_forecast_scale_cap import (
    volAttenForecastScaleCap,
)
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
#动态系统
my_system.accounts.optimised_portfolio().percent.curve().to_csv("/home/xiachenjun/sim_dynamic.csv")
#静态系统
my_system.accounts.portfolio().percent.curve().to_csv("/home/xiachenjun/sim.csv")
