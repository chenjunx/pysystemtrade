import matplotlib

matplotlib.use('WebAgg')
import matplotlib.pyplot as plt
import backtrader as bt
import backtrader.feeds as btfeeds
from backtrader.comminfo import CommInfoBase
from backtrader.comminfo import CommissionInfo
import datetime
from datetime import timedelta

import backtrader.plot

plt.switch_backend('WebAgg')

data = btfeeds.GenericCSVData(
    dataname='/Users/xiachenjun/workfiles/trade/data/btc_huobi_2018_2019_5_1min.csv',
    # dataname='/Users/xiachenjun/workfiles/trade/data/btc_huobi_2018_1min_demo.csv',
    fromdate=datetime.datetime(2018, 1, 1, 0, 0),
    todate=datetime.datetime(2019, 1, 1, 23, 59),
    nullvalue=0.0,
    dtformat=('%Y/%m/%d %H:%M'),
    datetime=0,
    high=1,
    low=3,
    open=2,
    close=4,
    volume=5,
    openinterest=-1,
    timeframe=bt.TimeFrame.Minutes
)


# Create a Stratey
class TestStrategy(bt.Strategy):
    params = (
        ('printlog', True),
    )

    def log(self, txt, dt=None, doprint=False):
        ''' Logging function for this strategy'''
        if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.datetime(0)
            print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.initvalue = 10000
        pass

    def next(self):
        pass

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return
            # Check if an order has been completed
            # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f,size %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm,
                     order.executed.size))
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f,size %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm,
                          order.executed.size))
                self.initcash = self.broker.get_value()
            self.bar_executed = len(self)

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def stop(self):
        self.log(' Ending Value %.2f' % (self.broker.getvalue()), doprint=True)

    def stop(self):
        self.log(' Ending Value %.2f' % (self.broker.getvalue()), doprint=True)


comminfo = bt.CommissionInfo(commtype=bt.CommissionInfo.COMM_PERC,  # % commission
                             commission=0.0012,  # 0.12%
                             )

cerebro = bt.Cerebro(cheat_on_open=True)
cerebro.broker.addcommissioninfo(comminfo)
cerebro.adddata(data)
cerebro.addstrategy(TestStrategy)
cerebro.broker.setcash(10000.0)
cerebro.addwriter(bt.WriterFile, csv=True, out="./trade_detail/btc_hans_1min.csv")
cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='SharpeRatio')
cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='AnnualReturn')
cerebro.addobserver(bt.observers.BuySell)

# Run over everything
results = cerebro.run()
strat = results[0]
print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
print('AnnualReturn:', strat.analyzers.AnnualReturn.get_analysis())
print('sharpratio:', strat.analyzers.SharpeRatio.get_analysis())
# Plot the result
# cerebro.plot()
