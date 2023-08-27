# QTBUY

## Binance Trading Bot
Binance GUI Trade Bot

![image](https://github.com/Mizogg/QTBUY/assets/88630056/88cdfac4-25dd-4520-94d0-0fbc2892abbe)

## Overview

This repository contains the source code for a cryptocurrency trading bot that interacts with the Binance exchange using the Binance API. The bot is designed to automate the process of buying and selling cryptocurrency pairs based on specific criteria, such as profit margin, price thresholds, and more.

## Features

- Automated trading of cryptocurrency pairs on Binance exchange.
- Real-time monitoring of market conditions and price movements.
- Calculating and adjusting order quantities to meet Binance's minimum notional requirements.
- Setting up profit margins and price thresholds for safe trading.
- Utilizing candlestick data to make informed trading decisions.
- User interface built using PyQt for user-friendly configuration and control.
- Logging system to track trading activities and errors.
- Support for multiple trading pairs and adjustable trading caps.

```
[XRPUSDT]Sell Order Not Filled at {'symbol': 'XRPUSDT', 'orderId': 5471633871, 'orderListId': -1, 'clientOrderId': '12321321312313312', 'price': '0.52210000', 'origQty': '12.00000000', 'executedQty': '0.00000000', 'cummulativeQuoteQty': '0.00000000', 'status': 'NEW', 'timeInForce': 'GTC', 'type': 'LIMIT', 'side': 'BUY', 'stopPrice': '0.00000000', 'icebergQty': '0.00000000', 'time': 1692647896967, 'updateTime': 1692647896967, 'isWorking': True, 'workingTime': 1692647896967, 'origQuoteOrderQty': '0.00000000', 'selfTradePreventionMode': 'NONE'} will keep watching 
[XRPUSDT] Placed Sell Order at 0.5231 for 12.0
[XRPUSDT] Sell Order Not Filled at 0.5231 will keep watching 
[XRPUSDT] Sell Order Not Filled at 0.5231 will keep watching 
[XRPUSDT] Sell Order Not Filled at 0.5231 will keep watching 
[XRPUSDT] Sell Order Not Filled at 0.5231 will keep watching 
[XRPUSDT] Sell Order Not Filled at 0.5231 will keep watching 
[XRPUSDT] Sell Order Not Filled at 0.5231 will keep watching
[XRPUSDT] Sell Order Not Filled at 0.5231 will keep watching
[XRPUSDT] Sell Order Filled at 0.5231
[XRPUSDT] Available USDT Balance for trading = 15.57 $
[XRPUSDT] Available USDT Balance = 31.14 $
[XRPUSDT] Current Best Buy Price = 0.52 $
[XRPUSDT] Calculated Sell Price = 0.5238
[XRPUSDT] Available USDT Balance = 31.14445475
[XRPUSDT] Placed Buy Order at 0.5228 for 12.00000000
[XRPUSDT]Sell Order Not Filled at {'symbol': 'XRPUSDT', 'orderId': 5471646791, 'orderListId': -1, 'clientOrderId': '12321321312313312', 'price': '0.52280000', 'origQty': '12.00000000', 'executedQty': '0.00000000', 'cummulativeQuoteQty': '0.00000000', 'status': 'NEW', 'timeInForce': 'GTC', 'type': 'LIMIT', 'side': 'BUY', 'stopPrice': '0.00000000', 'icebergQty': '0.00000000', 'time': 1692648158713, 'updateTime': 1692648158713, 'isWorking': True, 'workingTime': 1692648158713, 'origQuoteOrderQty': '0.00000000', 'selfTradePreventionMode': 'NONE'} will keep watching 
```

https://github.com/Mizogg/QTBUY/assets/88630056/ee9a51bf-982b-4de9-99f2-3ac80762a2b9

## Getting Started

1. Clone the repository: `git clone https://github.com/Mizogg/QTBUY.git`
2. Install the required dependencies: `pip install -r requirements.txt`
3. Set up your Binance API credentials by updating `API_KEY` and `API_SECRET` in the code.
4. Configure your trading pairs and settings using the user interface.
5. Run the bot: `python trading_bot.py`
6. Monitor the bot's output and logs for trading activities.

## Usage

- The bot's user interface allows you to configure the trading pairs you want to trade and set various trading parameters such as profit margins and trading caps.
- When you start the bot, it will automatically place buy and sell orders based on the configured parameters.
- The bot continuously monitors market conditions, price movements, and order execution, making informed decisions about trading activities.
- Use the provided logging system to track the bot's activities, errors, and trading outcomes.
Remember, trading can be profitable in range-bound markets but might lead to losses in strongly trending markets. Always monitor your bot's performance and adjust your strategy as needed.

![image](https://github.com/Mizogg/QTBUY/assets/88630056/c9df37ef-5207-4029-8365-acca1b1f2b59)

## Contributing

Contributions to this project are welcome! If you find any bugs or have suggestions for improvements, please feel free to open an issue or submit a pull request.

## Disclaimer

Please be aware that trading cryptocurrencies involves risks and is not suitable for all investors. This trading bot is provided for educational purposes and should not be used for real trading without thorough testing and understanding of its behavior.

Testing: Always test thoroughly in a sandbox environment or with small amounts before committing significant capital.

**Disclaimer: Trading involves substantial risk and is not suitable for every investor. The trading bot provided in this repository is for educational and informational purposes only. Before using the trading bot, it is strongly recommended that you thoroughly test it in a safe environment with paper trading or small amounts of capital.**

**Warning: The trading bot provided in this repository can execute real trades on the Binance exchange. There is a risk of financial loss associated with trading, and the trading bot may not always yield profitable results.**

**By using this trading bot, you acknowledge and understand that:**
- The trading bot is provided "as is" without any warranties or guarantees.
- You will not hold the author or contributors responsible for any losses incurred while using the trading bot.
- You are solely responsible for the decisions you make based on the bot's output.
- You have read and understood the Binance API documentation and terms of use.

It is strongly recommended that you:
- Thoroughly review and understand the code before using the trading bot.
- Test the trading bot with paper trading or small amounts of capital before executing real trades.
- Keep your API keys and sensitive information secure and do not share them with anyone.
- Monitor the trading bot's behavior and performance closely.

Remember that past performance is not indicative of future results. Only trade with capital that you can afford to lose.**

**By using the trading bot, you agree to these terms and acknowledge the risks associated with trading.**


## License

This project is licensed under the [MIT License](LICENSE).
