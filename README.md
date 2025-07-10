# Advanced Binance Futures Trading Bot

A comprehensive CLI-based trading bot for Binance Futures with support for multiple order types, advanced strategies, and robust logging.

## Features

### Basic Orders (50% Weight)
- **Market Orders**: Immediate execution at current market price
- **Limit Orders**: Execute at specified price or better
- Input validation and error handling
- Real-time order status tracking

### Advanced Orders (30% Weight)
- **Stop-Limit Orders**: Conditional orders triggered at stop price
- **OCO Orders**: One-Cancels-Other (custom implementation for futures)
- **TWAP Orders**: Time-Weighted Average Price (split large orders over time)
- **Grid Orders**: Automated buy-low/sell-high within price range

### Logging & Validation (10% Weight)
- Structured logging with timestamps
- Order action tracking
- API call logging
- Error traces and debugging
- Input validation for all parameters

### Utilities & Management (10% Weight)
- Account balance checking
- Open orders management
- Order history viewing
- Order cancellation
- Performance metrics

## Installation

1. **Clone or extract the project:**
   ```bash
   cd binance_bot
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your API credentials:**
   
   **Option 1: Environment Variables (Recommended)**
   ```bash
   set BINANCE_API_KEY=your_api_key_here
   set BINANCE_SECRET_KEY=your_secret_key_here
   ```
   
   **Option 2: Command Line Arguments**
   ```bash
   python main.py --api-key YOUR_API_KEY --secret-key YOUR_SECRET_KEY
   ```

## Usage

### Basic Usage
```bash
python main.py
```

### With Testnet (Recommended for testing)
```bash
python main.py --testnet
```

### With API Keys
```bash
python main.py --api-key YOUR_API_KEY --secret-key YOUR_SECRET_KEY --testnet
```

## Menu Options

1. **Market Order** - Execute immediately at market price
2. **Limit Order** - Execute at specific price
3. **Stop-Limit Order** - Conditional execution with stop and limit prices
4. **OCO Order** - One-Cancels-Other with take profit and stop loss
5. **TWAP Order** - Split large orders over time
6. **Grid Order** - Automated grid trading strategy
7. **Check Account Balance** - View current balances
8. **Check Open Orders** - List all open orders
9. **Cancel Order** - Cancel specific order
10. **View Order History** - Show recent order history

## Order Types Explained

### Market Orders
- **Purpose**: Immediate execution
- **Use Case**: Quick entry/exit
- **Parameters**: Symbol, Side (BUY/SELL), Quantity

### Limit Orders
- **Purpose**: Execute at specific price or better
- **Use Case**: Precise entry/exit points
- **Parameters**: Symbol, Side, Quantity, Price

### Stop-Limit Orders
- **Purpose**: Conditional execution with price protection
- **Use Case**: Risk management, breakout trading
- **Parameters**: Symbol, Side, Quantity, Stop Price, Limit Price

### OCO Orders
- **Purpose**: Automatic profit-taking and loss-cutting
- **Use Case**: Position management
- **Parameters**: Symbol, Side, Quantity, Take Profit Price, Stop Loss Price

### TWAP Orders
- **Purpose**: Reduce market impact of large orders
- **Use Case**: Large position building/liquidation
- **Parameters**: Symbol, Side, Total Quantity, Duration, Interval

### Grid Orders
- **Purpose**: Profit from price oscillations
- **Use Case**: Range-bound markets
- **Parameters**: Symbol, Grid Levels, Price Range, Total Quantity

## File Structure

```
binance_bot/
├── main.py                 # Main CLI application
├── src/
│   ├── binance_client.py   # Binance API client
│   ├── market_orders.py    # Market order logic
│   ├── limit_orders.py     # Limit order logic
│   ├── validator.py        # Input validation
│   ├── logger.py          # Logging system
│   └── advanced/
│       ├── oco.py         # OCO order logic
│       ├── twap.py        # TWAP strategy
│       ├── stop_limit.py  # Stop-limit orders
│       └── grid.py        # Grid trading
├── bot.log                # Application logs
├── requirements.txt       # Dependencies
└── README.md             # This file
```

## Configuration

### API Permissions Required
- Futures Trading
- Read Account Information
- Place Orders
- Cancel Orders

### Rate Limits
The bot respects Binance rate limits and includes automatic delays between requests.

### Risk Management
- Input validation on all parameters
- Price and quantity bounds checking
- Balance verification before order placement
- Maximum order size limits

## Logging

All bot activities are logged to `bot.log` with the following information:
- Timestamp
- Order placements and executions
- API calls and responses
- Error messages and stack traces
- Performance metrics

## Example Usage

### Place a Market Order
1. Run the bot: `python main.py --testnet`
2. Select option `1` (Market Order)
3. Enter symbol: `BTCUSDT`
4. Enter side: `BUY`
5. Enter quantity: `0.001`
6. Confirm execution

### Place a Grid Order
1. Select option `6` (Grid Order)
2. Enter symbol: `BTCUSDT`
3. Enter grid levels: `10`
4. Enter min price: `30000`
5. Enter max price: `35000`
6. Enter total quantity: `0.01`
7. Confirm execution

## Safety Features

- **Testnet Support**: Test strategies without real money
- **Input Validation**: Comprehensive parameter checking
- **Error Handling**: Graceful failure and recovery
- **Logging**: Complete audit trail
- **Rate Limiting**: Automatic API rate management

## Troubleshooting

### Common Issues

1. **API Key Errors**
   - Verify API key and secret are correct
   - Check API permissions include futures trading
   - Ensure IP whitelist includes your IP (if configured)

2. **Order Placement Failures**
   - Check account balance
   - Verify symbol is correct and tradeable
   - Ensure quantity meets minimum requirements

3. **Connection Issues**
   - Check internet connectivity
   - Verify Binance API is accessible
   - Try using testnet for testing

### Getting Help

1. Check the `bot.log` file for detailed error messages
2. Verify your API credentials and permissions
3. Test with small amounts on testnet first
4. Ensure all dependencies are installed correctly

## Disclaimer

This bot is for educational and research purposes. Always:
- Test thoroughly on testnet before live trading
- Start with small amounts
- Monitor your positions actively
- Understand the risks involved in futures trading
- Use proper risk management

Trading cryptocurrency futures involves substantial risk and may not be suitable for all investors.
