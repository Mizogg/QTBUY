import time, sys
from binance.client import Client
from PyQt6.QtWidgets import QApplication, QVBoxLayout, QHBoxLayout, QWidget, QLineEdit, QPushButton, QTextEdit, QSlider, QLabel, QGridLayout, QMessageBox, QGroupBox, QSpinBox
from PyQt6.QtCore import pyqtSlot, QThread, pyqtSignal, Qt, QTimer, QElapsedTimer
from PyQt6.QtGui import QIcon
import logging
from datetime import datetime
import math

# Setup logging
logging.basicConfig(filename='app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

# Binance API credentials
API_KEY = 'API_KEY'
API_SECRET = 'API_SECRET'

client = Client(API_KEY, API_SECRET)

def get_lot_size(symbol):
    exchange_info = client.get_exchange_info()
    for s in exchange_info['symbols']:
        if s['symbol'] == symbol:
            for f in s['filters']:
                if f['filterType'] == 'LOT_SIZE':
                    return float(f['minQty']), float(f['maxQty']), float(f['stepSize'])
    return None, None, None

def adjust_order_qty_based_on_lot_size(order_qty, min_qty, max_qty, step_size):
    if order_qty < min_qty:
        return min_qty
    elif order_qty > max_qty:
        return max_qty
    else:
        return (order_qty // step_size) * step_size

def get_min_notional(symbol):
    """
    Fetch the MIN_NOTIONAL value for a given symbol.
    """
    try:
        # Fetch the exchange information for the symbol
        exchange_info = client.get_exchange_info()
        #logging.info(f"Exchange Info for {symbol}: {exchange_info}")  # Log the entire response
        
        for s in exchange_info['symbols']:
            if s['symbol'] == symbol:
                for filter in s['filters']:
                    if filter['filterType'] == 'NOTIONAL':
                        return float(filter['minNotional'])
        return None
    except Exception as e:
        logging.error(f"An error occurred while fetching MIN_NOTIONAL for {symbol}: {str(e)}")
        return None
       
class Worker(QThread):
    update_signal = pyqtSignal(str)

    def __init__(self, trade_func):
        super().__init__()
        self.trade_func = trade_func
        self.is_running = True

    def run(self):
        while self.is_running:
            for symbol in self.symbols:
                self.trade_func(symbol)
                self.sleep(3)

    def stop(self):
        self.is_running = False

def adjust_price(price, tick_size):
    precision = int(round(-math.log(tick_size, 10), 0))
    return round(price, precision)
    
class TradingBotApp(QWidget):
    def __init__(self):
        super().__init__()
        self.symbols = []
        self.workers = {}
        self.coin_input_fields = {}
        self.coin_input_fields1 = {}
        self.pending_orders = {}
        self.quantity = '0.0001'
        self.PROFIT_MARGIN = 0.001
        self.PRICE_INCREASE_THRESHOLD = 0.05
        self.PRICE_CHECK_TIMEFRAME = 3600
        self.last_prices = {symbol: None for symbol in self.symbols}
        self.last_price_time = {symbol: None for symbol in self.symbols}
        self.timer = QTimer(self)
        self.start_time = QElapsedTimer()
        self.init_ui()
        self.worker = None

    def init_ui(self):
        self.setGeometry(70, 70, 900, 800)
        self.setWindowTitle('QT BUYBUY.py')
        self.setWindowIcon(QIcon('miz.ico'))
        self.setStyleSheet("font-size: 17px; font-family: Calibri;")
        layout = QVBoxLayout()
        welcome_label = QLabel("GUI Mizogg Trading")
        welcome_label.setStyleSheet("font-size: 24px; font-weight: bold; color: purple;")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(welcome_label)
        # Create Symbol input text box
        self.symbol_input = QLineEdit(self)
        self.symbol_input.setPlaceholderText("Enter symbols separated by space or comma (e.g., YGGUSDT, XRPUSDT)")
        layout.addWidget(self.symbol_input)

        self.grid_layout = QGridLayout()
        row = 0
        for symbol, input_field in self.coin_input_fields.items():
            self.grid_layout.addWidget(QLabel(symbol), row, 0)
            self.grid_layout.addWidget(input_field, row, 1)
            row += 1
        layout.addLayout(self.grid_layout)
        
        self.grid_layout1 = QGridLayout()
        row = 0
        for symbol, input_field1 in self.coin_input_fields1.items():
            self.grid_layout1.addWidget(QLabel(symbol), row, 0)
            self.grid_layout1.addWidget(input_field1, row, 1)
            row += 1
        layout.addLayout(self.grid_layout1)
        # Create Check Price button
        self.check_price_button = QPushButton("Check Best Buy Price - Profit Amount - Trade Amount", self)
        self.check_price_button.setStyleSheet("color: blue; font-size: 20px;")
        self.check_price_button.setToolTip("Click me to refresh data")
        self.check_price_button.clicked.connect(self.on_check_price)
        layout.addWidget(self.check_price_button)

        # Create Profit Margin Slider
        self.profit_margin_label = QLabel(self)
        self.profit_margin_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.profit_margin_slider.setMinimum(0)
        self.profit_margin_slider.setMaximum(100)
        self.profit_margin_slider.setValue(int(self.PROFIT_MARGIN * 1000))
        self.profit_margin_slider.valueChanged.connect(self.update_profit_margin)
        self.update_profit_margin(self.profit_margin_slider.value())

        layout.addWidget(self.profit_margin_label)
        layout.addWidget(self.profit_margin_slider)
        
        
        # Create the group box
        group_box = QGroupBox("Additional Options")
        group_box.setStyleSheet("QGroupBox { border: 3px solid blue; padding: 15px; }")

        # Create the widgets
        percent_label = QLabel("% Available USDT Balance for trading")
        self.percent_input = QSpinBox()
        self.percent_input.setRange(10, 100)
        self.percent_input.setSingleStep(10)
        self.percent_input.setValue(50)
        self.percent_input.valueChanged.connect(self.update_percentage)
        self.current_percentage = self.percent_input.value()

        percent_label_labelTrading = QLabel('Trading Balance:')
        percent_label_labelTrading.setStyleSheet("font-size: 14px; font-weight: bold; color: black;")
        self.percent_editTrading = QLineEdit()
        self.percent_editTrading.setReadOnly(True)
        
        percent_label_labelAvailable = QLabel('Available Balance:')
        percent_label_labelAvailable.setStyleSheet("font-size: 14px; font-weight: bold; color: black;")
        self.percent_editAvailable = QLineEdit()
        self.percent_editAvailable.setReadOnly(True)
        
        # Create a layout for the widgets inside the group box
        group_layout = QHBoxLayout()
        group_layout.addWidget(percent_label)
        group_layout.addWidget(self.percent_input)
        group_layout.addWidget(percent_label_labelAvailable)
        group_layout.addWidget(self.percent_editAvailable)
        group_layout.addWidget(percent_label_labelTrading)
        group_layout.addWidget(self.percent_editTrading)
        
        # Set the group layout
        group_box.setLayout(group_layout)

        layout.addWidget(group_box)


        # Create Start Trading button
        self.start_button = QPushButton("Start Trading Make Sure Everything IS Correct Before Starting", self)
        self.start_button.setToolTip("WARNING MAKE SURE READY!!!")
        self.start_button.setStyleSheet("color: orange; font-size: 20px;")
        self.start_button.clicked.connect(self.on_start)

        # Create Stop Trading button
        self.stop_button = QPushButton("Stop Trading", self)
        self.stop_button.setToolTip("Stop the trading process Warning Use With Care")
        self.stop_button.setStyleSheet("color: red; font-size: 20px;")
        self.stop_button.clicked.connect(self.on_stop)

        # Add both buttons to a QHBoxLayout
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)

        # Add the button layout to the main layout
        layout.addLayout(button_layout)

        # Create a QHBoxLayout for buttons
        buttons_layout = QHBoxLayout()

        # Create Display Orders button
        self.display_orders_button = QPushButton("Display All Orders", self)
        self.display_orders_button.setToolTip("Display all orders that you Currently Have.")
        self.display_orders_button.setStyleSheet("color: blue; font-size: 20px;")

        self.display_orders_button.clicked.connect(self.display_all_orders)
        buttons_layout.addWidget(self.display_orders_button)

        # Create Cancel Pending Orders button
        self.cancel_button = QPushButton("Cancel Pending Orders", self)
        self.cancel_button.setToolTip("Cancel all pending buy orders Warning Use With Care")
        self.cancel_button.setStyleSheet("color: red; font-size: 20px;")

        self.cancel_button.clicked.connect(self.show_cancel_orders_confirmation)
        buttons_layout.addWidget(self.cancel_button)

        # Add the buttons layout to the main layout
        layout.addLayout(buttons_layout)

       # Create a QGroupBox
        self.output_groupBox = QGroupBox(self)
        self.output_groupBox.setTitle("Trading Pre Checks")
        self.output_groupBox.setStyleSheet("QGroupBox { border: 3px solid blue; padding: 15px; }")

        # Create layout for the QGroupBox
        self.output_layout = QVBoxLayout(self.output_groupBox)

        # Create QTextEdit
        self.output = QTextEdit(self)
        self.output.setReadOnly(True)

        # Add QTextEdit to the QGroupBox's layout
        self.output_layout.addWidget(self.output)

        # Add QGroupBox to the main layout
        layout.addWidget(self.output_groupBox)
        
        self.timer.timeout.connect(self.update_time_display)
        self.elapsed_time_label = QLabel("Elapsed Time: 00:00:00", self)
        layout.addWidget(self.elapsed_time_label)
        
        
        # Create output text area
        self.output_runBox = QGroupBox(self)
        self.output_runBox.setTitle("Trading Running Output")
        self.output_runBox.setStyleSheet("QGroupBox { border: 3px solid orange; padding: 15px; }")

        # Create layout for the QGroupBox
        self.output_runLayout = QVBoxLayout(self.output_runBox)

        # Create QTextEdit
        self.output_run = QTextEdit(self)
        self.output_run.setReadOnly(True)

        # Add QTextEdit to the QGroupBox's layout
        self.output_runLayout.addWidget(self.output_run)

        # Add QGroupBox to the main layout
        layout.addWidget(self.output_runBox)

        self.setLayout(layout)
    
    def update_time_display(self):
        elapsed_time = self.start_time.elapsed() // 1000  # Convert milliseconds to seconds
        hours = elapsed_time // 3600
        minutes = (elapsed_time % 3600) // 60
        seconds = elapsed_time % 60
        self.elapsed_time_label.setText(f"Elapsed Time: {hours:02}:{minutes:02}:{seconds:02}")
    
    def show_error_message(self, title, message):
        error_box = QMessageBox(self)
        error_box.setWindowTitle(title)
        error_box.setWindowIcon(QIcon('miz.ico'))
        error_box.setIcon(QMessageBox.Icon.Warning)
        error_box.setText(message)
        error_box.exec()
    
    def display_all_orders(self):

        all_orders = []

        for symbol in self.symbols:
            orders = client.get_all_orders(symbol=symbol)
            all_orders.extend(orders)

        if all_orders:
            orders_text = "\n".join([f"Symbol: {order['symbol']}, Side: {order['side']}, Status: {order['status']}" for order in all_orders])
            msgBox = QMessageBox(self)
            msgBox.setWindowTitle("All Orders")
            msgBox.setWindowIcon(QIcon('miz.ico'))
            msgBox.setIcon(QMessageBox.Icon.Information)
            msgBox.setText(f"All Orders:\n{orders_text}")
            msgBox.exec()
        else:
            QMessageBox.warning(self, "No Orders", "There are no orders in your account.")
    
    def determine_best_buy_price(self, symbol):
        if not symbol:
            self.show_error_message("Input Trading Currency", "Please input the trading currency.")
            return None
        # Fetch the current best buy price from the order book
        order_book = client.get_order_book(symbol=symbol, limit=5)
        best_buy_price = float(order_book['bids'][0][0])

        # Log and append the output
        self.output.append(f'[{symbol}] Current Best Buy Price = {best_buy_price:.4f} $')
        logging.info(f'[{symbol}] Current Best Buy Price = {best_buy_price:.4f} $')

        return best_buy_price

    def calculate_order_qty(self, symbol, available_balance, best_buy_price):
        # Fetch LOT_SIZE filter requirements
        min_qty, max_qty, step_size = get_lot_size(symbol)

        # Calculate potential order quantity based on available USDT balance
        potential_order_qty = (available_balance) / best_buy_price  # 50% of available balance

        # Consider the maximum allowed quantity
        max_quantity_for_symbol = float(self.coin_input_fields[symbol].text())
    
        potential_order_qty = min(potential_order_qty, max_quantity_for_symbol)

        # Adjust order_qty based on LOT_SIZE filter requirements
        order_qty = adjust_order_qty_based_on_lot_size(potential_order_qty, min_qty, max_qty, step_size)

        return order_qty, min_qty, max_qty
        
    @pyqtSlot()
    def show_cancel_orders_confirmation(self):
        # Create the confirmation message
        confirmation_msg = "Are you sure you want to cancel all pending buy orders?\n\n"
        for symbol in self.pending_orders:
            order_id = self.pending_orders[symbol]
            if order_id is not None:
                confirmation_msg += f"Cancel order for {symbol}\n"

        # Display the confirmation dialog
        confirmation_box = QMessageBox(self)
        confirmation_box.setWindowTitle("Confirm Cancel Orders")
        confirmation_box.setWindowIcon(QIcon('miz.ico'))
        confirmation_box.setIcon(QMessageBox.Icon.Question)
        confirmation_box.setText(confirmation_msg)
        confirmation_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        confirmation_box.setDefaultButton(QMessageBox.StandardButton.No)
        response = confirmation_box.exec()

        # Check the user's decision
        if response == QMessageBox.StandardButton.No:
            return

    @pyqtSlot()
    def on_stop(self):
        if self.worker is not None:
            # Ask for confirmation to stop trading
            confirmation_box = QMessageBox(self)
            confirmation_box.setWindowTitle("Confirmation")
            confirmation_box.setText("Are you sure you want to stop trading?")
            confirmation_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            confirmation_box.setDefaultButton(QMessageBox.StandardButton.No)
            response = confirmation_box.exec()

            if response == QMessageBox.StandardButton.Yes:
                self.worker.stop()
                self.worker = None
                self.timer.stop()
                self.start_button.setText("Start Trading")
                self.stop_button.setEnabled(False)  # Disable the Stop button
                self.output_run.append("Trading stopped.")
        else:
            QMessageBox.warning(self, "No Active Trading", "There is no active trading to stop.")

    def update_percentage(self):
        self.current_percentage = self.percent_input.value()
    
    def fetch_and_display_balance(self, symbol):
        # Fetch the balance
        balance = client.get_asset_balance(asset='USDT')
        available_balance = float(balance['free'])
        percentage = self.current_percentage
        # Use 50% of the available balance for this trade
        trade_balance = (percentage / 100) * available_balance

        # Log and append the output
        self.percent_editTrading.setText(f'${trade_balance:.2f}')
        self.output.append(f'[{symbol}] Available USDT Balance for trading = ${trade_balance:.2f}')
        logging.info(f'[{symbol}] Available USDT Balance for trading = ${trade_balance:.2f}')
        self.percent_editAvailable.setText(f'${available_balance:.2f}')
        self.output.append(f'[{symbol}] Available USDT Balance = ${available_balance:.2f}')
        logging.info(f'[{symbol}] Available USDT Balance = ${available_balance:.2f}')

        return available_balance, trade_balance
        
    @pyqtSlot()
    def on_start(self):
        if self.worker is None:  # If no trading is currently active
            # Retrieve the necessary details
            symbol = self.symbol_input.text()
            best_buy_price = self.determine_best_buy_price(symbol)
            sale_price = best_buy_price * (1 + self.PROFIT_MARGIN)  # Calculated Sell Price
            available_balance, _ = self.fetch_and_display_balance(symbol)
            order_qty, _, _ = self.calculate_order_qty(symbol, available_balance, best_buy_price)
            amount_spent = best_buy_price * order_qty
            profit = (sale_price - best_buy_price) * order_qty
            expected_return = sale_price * order_qty  # Since this is a sale, it's the same as the total sale amount

            # Create the confirmation message
            msg_text = (f"Coin: {symbol}\n"
                        f"Buy Price: ${best_buy_price:.4f}\n"
                        f"Sale Price: ${sale_price:.4f}\n"
                        f"Amount Being Bought: {order_qty:.8f}\n"
                        f"Amount Being Spent: ${amount_spent:.4f}\n"
                        f"Expected Profit: ${profit:.4f}\n"
                        f"Expected Total Return (from sale): ${expected_return:.4f}\n\n"
                        f"Are you sure you want to start trading?")
            msg_text1 = (f"Coin: {symbol}\n"
                         f"Buy Price: ${best_buy_price:.4f}\n"
                         f"Sale Price: ${sale_price:.4f}\n"
                         f"Amount Being Bought: {order_qty:.8f}\n"
                         f"Amount Being Spent: ${amount_spent:.4f}\n"
                         f"Expected Profit: ${profit:.4f}\n"
                         f"Expected Total Return (from sale): ${expected_return:.4f}\n\n")
            # Display the confirmation dialog with the created message
            msgBox = QMessageBox(self)
            msgBox.setWindowTitle("Confirmation")
            msgBox.setText(msg_text)
            msgBox.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msgBox.setDefaultButton(QMessageBox.StandardButton.No)
            response = msgBox.exec()
            # Check the user's decision
            if response == QMessageBox.StandardButton.No:
                return
            # Process the symbols from the input
            symbols_text = self.symbol_input.text()
            self.output.append(msg_text1)
            if ',' in symbols_text:
                self.symbols = [symbol.strip() for symbol in symbols_text.split(',')]
            else:
                self.symbols = symbols_text.split()
            if symbol in self.pending_orders:
                self.output_run.append(f'[{symbol}] A buy order is already pending for this symbol. Skipping.')
                logging.info(f'[{symbol}] A buy order is already pending for this symbol. Skipping.')
                return
            # Start the trading process
            self.start_time.start()
            self.timer.start(1000) 
            self.worker = Worker(self.trade)
            self.worker.symbols = self.symbols
            self.worker.update_signal.connect(self.output_run.append)
            self.worker.start()
            self.start_button.setText("Stop Trading")
            self.stop_button.setEnabled(True)  # Enable the Stop button
        else:
            # Stop the trading process
            self.worker.stop()
            self.worker = None
            self.timer.stop()
            self.start_button.setText("Start Trading")
            self.stop_button.setEnabled(False)  # Disable the Stop button
            self.output_run.append("Trading stopped.")

    @pyqtSlot(int)
    def update_profit_margin(self, value):
        self.PROFIT_MARGIN = value / 1000.0
        percent_profit = self.PROFIT_MARGIN * 100
        self.profit_margin_label.setText(f"Profit Margin: {self.PROFIT_MARGIN:.3f} ({percent_profit:.2f}%)")

    
    @pyqtSlot()
    def on_check_price(self):
        # Process the symbols from the input
        symbols_text = self.symbol_input.text()
        if not symbols_text:
            self.show_error_message("Input Trading Currency", "Please input the trading currency.")
            return None
        if ',' in symbols_text:
            symbols = [symbol.strip() for symbol in symbols_text.split(',')]
        else:
            symbols = symbols_text.split()

        for symbol in symbols:
            self.check_best_buy_price(symbol)
            if symbol not in self.coin_input_fields:
                coin_label = QLabel(symbol, self)
                coin_input = QLineEdit(self)
                coin_input.setPlaceholderText(f"Max Quantity for {symbol}")
                self.coin_input_fields[symbol] = coin_input
            
                self.grid_layout.addWidget(coin_label)
                self.grid_layout.addWidget(coin_input)
                
            if  symbol not in self.coin_input_fields1:
                coin_input1 = QLineEdit(self)
                coin_input1.setPlaceholderText(f"Trading Cap for {symbol}")
                self.coin_input_fields1[symbol] = coin_input1
                
                self.grid_layout1.addWidget(coin_input1)
    
    def check_best_buy_price(self, symbol):
        try:
            order_book = client.get_order_book(symbol=symbol, limit=5)
            best_buy_price = float(order_book['bids'][0][0])
            min_notional = get_min_notional(symbol)

            # Calculate the sell price using the profit margin
            sell_price = "{:.4f}".format(best_buy_price * (1 + self.PROFIT_MARGIN))

            # Displaying both best buy price and calculated sell price
            self.output.append(f'[{symbol}] Current Best Buy Price = ${best_buy_price:.4f}, Calculated Sell Price = ${sell_price}')
            logging.info(f'[{symbol}] Current Best Buy Price = ${best_buy_price:.4f}, Calculated Sell Price = ${sell_price}')
            
            # Fetch the balance
            balance = client.get_asset_balance(asset='USDT')
            available_balance = float(balance['free'])
            # Use 50% of the available balance for this trade
            percentage = self.current_percentage
            trade_balance = (percentage / 100) * available_balance
            self.percent_editTrading.setText(f'${trade_balance:.2f}')
            self.output.append(f'[{symbol}] Available USDT Balance for trading = ${trade_balance:.2f}')
            logging.info(f'[{symbol}] Available USDT Balance for trading = ${trade_balance:.2f}')
            self.percent_editAvailable.setText(f'${available_balance:.2f}')
            self.output.append(f'[{symbol}] Available USDT Balance = ${available_balance:.2f}')
            logging.info(f'[{symbol}] Available USDT Balance = ${available_balance:.2f}')
            
            if min_notional is not None:
                self.output.append(f'[{symbol}] Minimum Notional Requirements for Order ${min_notional:.8f}')
                logging.info(f'[{symbol}] Minimum Notional Requirements for Order ${min_notional:.8f}')
            else:
                self.output.append(f'[{symbol}] Unable to fetch MIN_NOTIONAL value.')
                logging.info(f'[{symbol}] Unable to fetch MIN_NOTIONAL value.')
            self.display_candlestick_data(symbol)

        except Exception as e:
            logging.error(f"An error occurred while fetching price for {symbol}: {str(e)}")
            self.output.append(f"An error occurred while fetching price for {symbol}: {str(e)}")
    
    def get_candlestick_data(self, symbol, interval, ago):
        candlesticks = client.get_historical_klines(symbol, interval, ago)
        if not candlesticks:
            return None
        last_candlestick = candlesticks[0]
        return {
            'Open': float(last_candlestick[1]),
            'High': float(last_candlestick[2]),
            'Low': float(last_candlestick[3]),
            'Close': float(last_candlestick[4]),
            'Volume': float(last_candlestick[5])
        }

    def display_candlestick_data(self, symbol):
        intervals = ["1m", "5m", "15m", "30m"]
        timeframes = ["1 minute ago UTC", "5 minutes ago UTC", "15 minutes ago UTC", "30 minutes ago UTC"]
        
        for interval, timeframe in zip(intervals, timeframes):
            data = self.get_candlestick_data(symbol, interval, timeframe)
            if data:
                self.output.append(f'[{symbol}] Candlestick data for {timeframe}:')
                self.output.append(f"Open: ${data['Open']:.8f}, High: ${data['High']:.8f}, Low: ${data['Low']:.8f}, Close: ${data['Close']:.8f}, Volume: {data['Volume']:.8f}")
                
    def trade(self, symbol):
        try:
            # Fetch the balance
            balance = client.get_asset_balance(asset='USDT')
            available_balance = float(balance['free'])
            percentage = self.current_percentage
            trade_balance = (percentage / 100) * available_balance

            self.output.append(f'[{symbol}] Available USDT Balance for trading = {trade_balance:.2f} $')
            logging.info(f'[{symbol}] Available USDT Balance for trading = {trade_balance:.2f} $')

            self.output.append(f'[{symbol}] Available USDT Balance = {available_balance:.2f} $')
            logging.info(f'[{symbol}] Available USDT Balance = {available_balance:.2f} $')
            order_book = client.get_order_book(symbol=symbol, limit=5)
            best_buy_price = float(order_book['bids'][0][0])
            self.output.append(f'[{symbol}] Current Best Buy Price = {best_buy_price:.2f} $')
            logging.info(f'[{symbol}] Current Best Buy Price = {best_buy_price:.2f} $')

            # Fetch LOT_SIZE filter requirements
            min_qty, max_qty, step_size = get_lot_size(symbol)

            # Calculate potential order quantity based on available USDT balance
            potential_order_qty = (trade_balance) / best_buy_price  # 50% of available balance
            
            # Consider the maximum allowed quantity
            max_quantity_for_symbol = float(self.coin_input_fields[symbol].text())
        
            potential_order_qty = min(potential_order_qty, max_quantity_for_symbol)
            # Adjust order_qty based on LOT_SIZE filter requirements
            order_qty = adjust_order_qty_based_on_lot_size(potential_order_qty, min_qty, max_qty, step_size)
            logging.info(f"Best Buy Price for {symbol}: {best_buy_price}, Type: {type(best_buy_price)}")
            logging.info(f"Order Quantity for {symbol}: {order_qty}, Type: {type(order_qty)}")
            # Ensure the order_qty is within the min_qty and max_qty bounds
            if order_qty < min_qty:
                self.output_run.append(f'[{symbol}] Order quantity {order_qty:.8f} does not meet the minimum lot size requirement of {min_qty:.8f}. Skipping trade.')
                logging.info(f'[{symbol}] Order quantity {order_qty:.8f} does not meet the minimum lot size requirement of {min_qty:.8f}. Skipping trade.')
                return
            elif order_qty > max_qty:
                self.output_run.append(f'[{symbol}] Order quantity {order_qty:.8f} exceeds the maximum allowed quantity of {max_qty:.8f}. Skipping trade.')
                logging.info(f'[{symbol}] Order quantity {order_qty:.8f} exceeds the maximum allowed quantity of {max_qty:.8f}. Skipping trade.')
                return   
            # Price check logic
            # Fetch the current time
            current_time = time.time()
            # Check if there's a last price for the symbol
            if self.last_prices.get(symbol) is not None:
                last_price_time = self.last_price_time.get(symbol)
                if last_price_time is not None:
                    time_elapsed = current_time - last_price_time
                    if time_elapsed <= self.PRICE_CHECK_TIMEFRAME:
                        price_increase = (best_buy_price - self.last_prices[symbol]) / self.last_prices[symbol]
                        if price_increase >= self.PRICE_INCREASE_THRESHOLD:
                            self.output_run.append(f"Skipping {symbol} due to rapid price increase of {price_increase*100:.2f}% in the last hour")
                            logging.info(f"Skipping {symbol} due to rapid price increase of {price_increase*100:.2f}% in the last hour")
                            return
                    else:
                        # Update last price time if the elapsed time is larger than PRICE_CHECK_TIMEFRAME
                        self.last_price_time[symbol] = current_time
            else:
                # Initialize last price and last price time
                self.last_prices[symbol] = best_buy_price
                self.last_price_time[symbol] = current_time
            
                trading_cap_for_symbol = float(self.coin_input_fields1[symbol].text())
                # Check against trading cap
                if best_buy_price > trading_cap_for_symbol:
                    self.output_run.append(f"Skipping {symbol} due to trading cap of {trading_cap_for_symbol}")
                    logging.info(f"Skipping {symbol} due to trading cap of {trading_cap_for_symbol}")
                    return

            sell_price = float("{:.4f}".format(best_buy_price * (1 + self.PROFIT_MARGIN)))
            self.output_run.append(f'[{symbol}] Calculated Sell Price = {sell_price}')
            logging.info(f'[{symbol}] Calculated Sell Price = {sell_price}')
            
            balance = client.get_asset_balance(asset='USDT')
            available_balance = float(balance['free'])
            self.output_run.append(f'[{symbol}] Available USDT Balance = {available_balance}')
            logging.info(f'[{symbol}] Available USDT Balance = {available_balance}')

            if available_balance < order_qty * best_buy_price:
                self.output_run.append(f"Insufficient balance for {symbol}. Required: {order_qty * best_buy_price:.8f}, Available: {available_balance:.8f}")
                logging.info(f"Insufficient balance for {symbol}. Required: {order_qty * best_buy_price:.8f}, Available: {available_balance:.8f}")
                return

            # Make sure you're using the rounded and compliant order_qty for placing orders
            buy_order = client.order_limit_buy(
                symbol=symbol,
                quantity="{:.8f}".format(order_qty),  # Convert order_qty to string with 8 decimal places
                price=str(best_buy_price)
            )
            self.output_run.append(f'[{symbol}] Placed Buy Order at {best_buy_price} for {order_qty:.8f}')
            logging.info(f'[{symbol}] Placed Buy Order at {best_buy_price} for {order_qty:.8f}')
            while True:
                order_status = client.get_order(
                    symbol=symbol,
                    orderId=buy_order['orderId']
                )
                
                if order_status['status'] == 'PARTIALLY_FILLED':
                    if float(order_status['executedQty']) / float(order_status['origQty']) > 0.8:
                        client.cancel_order(symbol=symbol, orderId=buy_order['orderId'])
                        self.output_run.append(f'[{symbol}] Order partially filled and canceled. Filled: {order_status["executedQty"]}')
                        logging.info(f'[{symbol}] Order partially filled and canceled. Filled: {order_status["executedQty"]}')
                        break

                if order_status['status'] == 'FILLED':
                    break
                else:
                    self.output_run.append(f'[{symbol}]Sell Order Not Filled at {order_status} will keep watching ')
                    logging.info(f'[{symbol}] Sell Order Not Filled at {order_status} will keep watching')
                time.sleep(10)

            filled_quantity = float(order_status['executedQty'])

            sell_order = client.order_limit_sell(
                symbol=symbol,
                quantity=str(filled_quantity),
                price=sell_price
            )
            self.output_run.append(f'[{symbol}] Placed Sell Order at {sell_price} for {filled_quantity}')
            logging.info(f'[{symbol}] Placed Sell Order at {sell_price} for {filled_quantity}')

            while True:
                order_status = client.get_order(
                    symbol=symbol,
                    orderId=sell_order['orderId']
                )
                if order_status['status'] == 'FILLED':
                    self.output_run.append(f'[{symbol}] Sell Order Filled at {sell_price}')
                    logging.info(f'[{symbol}] Sell Order Filled at {sell_price}')
                    break
                else:
                    self.output_run.append(f'[{symbol}] Sell Order Not Filled at {sell_price} will keep watching ')
                    logging.info(f'[{symbol}] Sell Order Not Filled at {sell_price} will keep watching ')
                time.sleep(10)

        except Exception as e:
            logging.info(f"An error occurred while trading {symbol}: {str(e)}")
            self.output_run.append(f"An error occurred while trading {symbol}: {str(e)}")

    def main(self):
        while self.trading_active:
            symbol = self.symbol_input.text()
            self.trade(symbol)
            time.sleep(3)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TradingBotApp()
    window.show()
    sys.exit(app.exec())