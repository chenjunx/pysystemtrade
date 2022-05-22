from systems.provided.example.simplesystem import simplesystem
from sysdata.config.configdata import Config
from sysdata.sim.db_futures_sim_data import dbFuturesSimData
from syslogdiag.emailing import send_mail_msg

def run_future_strategy():
    data = dbFuturesSimData()
    #固定参数期货
    # my_system=simplesystem(data=data,config=Config("/home/software/pysystemtrade/systems/provided/mills/mills_future.yaml"))
    #动态参数期货
    my_system=simplesystem(data=data,config=Config("/home/software/pysystemtrade/systems/provided/mills/mills_future_estimate.yaml"))
    str = ''
    for i in ["POLYETHYLENE","HC","JD","RB","CORNSTARCH","PVC","PP","SoybeanMeal","MAIZE","FG","TA","MA","SR","FU"]:
        str = str +i+"\n"+ my_system.combForecast.get_combined_forecast(i).tail(5).to_string() +"\n\n"
    send_mail_msg(str , "国内期货策略")