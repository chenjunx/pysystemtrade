from syscore.objects import arg_not_supplied
from syslogdiag.log_to_screen import logtoscreen


from sysbrokers.broker_fx_handling import brokerFxHandlingData


class millsFxHandlingData(brokerFxHandlingData):
    def __init__(self, log=logtoscreen("millsFXHandlingData")):
        super().__init__(log=log)

    def __repr__(self):
        return "mills FX handling data %s" % str(self.mills_client)

    def broker_fx_balances(self, account_id: str = arg_not_supplied) -> dict:
        return self.mills_client.broker_fx_balances(account_id)
