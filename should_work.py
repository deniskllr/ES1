from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.common import *
from ibapi.contract import Contract
from ibapi.order import *
import threading
import yfinance as yf
import time
from SPY_3_logic import buy_signal
import math

class IBapi(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.account_summary = {}
        self.next_order_id = None

    def accountSummary(self, reqId: int, account: str, tag: str, value: str, currency: str):
        ''' Called when the account information is returned from IB server '''
        print("AccountSummary. ReqId:", reqId, "Account:", account, 
              "Tag: ", tag, "Value:", value, "Currency:", currency)
        self.account_summary[tag] = value

    def accountSummaryEnd(self, reqId: int):
        ''' Called after all account summary data has been received '''
        #print("AccountSummaryEnd. Req Id: ", reqId)
        self.disconnect()

    def nextValidId(self, orderId: int):
        '''Called when the next valid order ID is received from TWS '''
        super().nextValidId(orderId)
        self.next_order_id = orderId
        print('The next valid order id is: ', self.next_order_id)

def get_price(symbol):
    ticker = yf.Ticker(symbol)
    todays_data = ticker.history(period='1d')
    return todays_data['Close'][0]

def run_loop(app):
    app.run()

def main():
    # Instanz der API-Wrapper-Klasse erstellen
    app = IBapi()

    # Verbindung zum IB-Server herstellen
    app.connect('127.0.0.1', 7497, 99)

    # Start the socket in a thread
    api_thread = threading.Thread(target=run_loop, args=(app,), daemon=True)
    api_thread.start()

    time.sleep(3)  # sleep for a few seconds to let the server send the next valid order ID

    # Auf die Order ID warten
    while app.next_order_id is None:
        print('Waiting for valid order ID...')
        time.sleep(1)

    # Account Summary abfragen
    app.reqAccountSummary(1, 'All', '$LEDGER:ALL')

    # Erstellen Sie das Contract-Objekt für die Apple-Aktie
    contract = Contract()
    contract.symbol = 'SPY5'
    contract.secType = 'STK'
    contract.exchange = 'SMART'
    contract.currency = 'USD'

    # requests current SPY5 price
    buy_price = get_price('SPY')
    print(buy_price)
    available_funds = float(app.account_summary["TotalCashBalance"])
    equity_exposure = float(app.account_summary["StockMarketValue"])
    ExchangeRate = float(app.account_summary["ExchangeRate"])
    print(available_funds)
    print(equity_exposure)
    print(ExchangeRate)
    
    if buy_signal(): 
        quantity = math.floor(available_funds / buy_price) # diese Funktion rundet eine Dezimalzahl ab
        print("I would by now!"+ " Quanity:", quantity)
        if quantity:
            # Erstellen Sie das Order-Objekt
            order = Order()
            order.action = 'BUY'
            order.totalQuantity = quantity
            order.orderType = 'MOC'
            order.eTradeOnly = False
            order.firmQuoteOnly = False

            # Platzieren Sie die Order
            app.placeOrder(app.next_order_id, contract, order)
        else:
            print("Enough market exposure for now!")
            print("Current market exposure: ")
            print((ExchangeRate*equity_exposure)/(ExchangeRate*equity_exposure+available_funds))

    time.sleep(3)  # sleep to allow order to be processed before disconnecting

    # disconnect after the order is placed
    app.disconnect()
if __name__ == "__main__":
    main()