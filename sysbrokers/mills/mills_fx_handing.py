from syscore.objects import arg_not_supplied
from syslogdiag.log_to_screen import logtoscreen


from sysbrokers.broker_fx_handling import brokerFxHandlingData
from sysbrokers.mills.mills_connection import connectionMills


class millsFxHandlingData(brokerFxHandlingData):
    def __init__(self, connection_Mills: connectionMills, log=logtoscreen("millsFXHandlingData")):
        self._connection_Mills = connection_Mills
        super().__init__(log=log)


    def __repr__(self):
        return "mills FX handling data %s" % str(self.mills_client)

    def broker_fx_balances(self, account_id: str = arg_not_supplied) -> dict:
        return self.mills_client.broker_fx_balances(account_id)
