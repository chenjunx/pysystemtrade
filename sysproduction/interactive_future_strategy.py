from systems.provided.example.simplesystem import simplesystem
from sysdata.config.configdata import Config
from sysdata.sim.db_futures_sim_data import dbFuturesSimData
from syslogdiag.emailing import send_mail_msg
from arctic import Arctic
import pymongo

def run_future_strategy():
    myclient = pymongo.MongoClient('mongodb://localhost:27017/')
    production = myclient['production']
    data = dbFuturesSimData()
    #固定参数期货
    # my_system=simplesystem(data=data,config=Config("/home/software/pysystemtrade/systems/provided/mills/mills_future.yaml"))
    #动态参数期货
    my_system=simplesystem(data=data,config=Config("/home/software/pysystemtrade/systems/provided/mills/mills_future_estimate.yaml"))
    msg = ''
    import pandas as pd
    # position = pd.read_csv('/home/software/pysystemtrade/sysproduction/pysystemtrader_position.csv')
    pysystemtrader_position = production["pysystemtrader_position"]
    position = pysystemtrader_position.find({"state": "o"})
    instruments = [
        {"code": "POLYETHYLENE", "name": "聚乙烯(塑料)"},
        {"code": "HC", "name": "热卷"},
        {"code": "JD", "name": "鸡蛋"},
        {"code": "RB", "name": "螺纹钢"},
        {"code": "CORNSTARCH", "name": "淀粉"},
        {"code": "PVC", "name": "聚氯乙烯"},
        {"code": "PP", "name": "聚丙烯"},
        {"code": "SoybeanMeal", "name": "豆粕"},
        {"code": "MAIZE", "name": "玉米"},
        {"code": "FG", "name": "玻璃"},
        {"code": "TA", "name": "PTA"},
        {"code": "MA", "name": "甲醇"},
        {"code": "SR", "name": "白糖"},
        {"code": "FU", "name": "燃油"}
    ]
    for i in instruments:
        ser = my_system.combForecast.get_combined_forecast(i['code'])
        i['forecast'] = ser[ser.size - 1]
    instruments_sorted = sorted(instruments, key=lambda i: abs(i['forecast']), reverse=True)
    store = Arctic('localhost')
    library = store['simple_foreast']
    for i in instruments_sorted:
        item = library.read(i['code'])
        data = item.data
        data1 = data.append(my_system.combForecast.get_combined_forecast(i['code']).tail(1))
        data1.drop_duplicates(inplace=True)
        pstr = ""
        for p in position:
            if p['symbol'] == i['code']:
                if p['symbol'] == i['code']:
                    pstr = pstr + str(p) + "\n"
        msg = msg + i['code'] + ' ' + i['name'] + "\n" + data1.to_string() + "\n" + pstr + "\n\n"
        library.write(i['code'], data1)
    send_mail_msg(msg, "国内期货策略")
    myclient.close()