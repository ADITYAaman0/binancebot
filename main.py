#!/usr/bin/env python3
"""
Advanced Binance Futures Trading Bot
CLI-based bot supporting multiple order types with robust logging and validation
"""

import sys
import os
import argparse
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from binance_client import BinanceClient
from market_orders import MarketOrderManager
from limit_orders import LimitOrderManager
from advanced.oco import OCOOrderManager
from advanced.twap import TWAPOrderManager
from advanced.stop_limit import StopLimitOrderManager
from advanced.grid import GridOrderManager
from logger import setup_logger
from validator import OrderValidator

class BinanceFuturesBot:
    def __init__(self, F8wmuzN5RQiQXZdLUh1rlzQGR2YDrUJuxHNblQS1fwbeblElqHjQxylg7CQSu6NL: str, Y5sg3jC1K8GYsP7vAgambxRzrNCqfbNa8HppuFxW8Q17TUJAASnF34l5KiJBRxyy: str, testnet: bool = False):
        """Initialize the Binance Futures Trading Bot"""
        self.logger = setup_logger('BinanceFuturesBot')
        self.logger.info("Initializing Binance Futures Bot")
        
        # Initialize Binance client
        self.client = BinanceClient(F8wmuzN5RQiQXZdLUh1rlzQGR2YDrUJuxHNblQS1fwbeblElqHjQxylg7CQSu6NL, Y5sg3jC1K8GYsP7vAgambxRzrNCqfbNa8HppuFxW8Q17TUJAASnF34l5KiJBRxyy, testnet)
        
        # Initialize order managers
        self.market_orders = MarketOrderManager(self.client)
        self.limit_orders = LimitOrderManager(self.client)
        self.oco_orders = OCOOrderManager(self.client)
        self.twap_orders = TWAPOrderManager(self.client)
        self.stop_limit_orders = StopLimitOrderManager(self.client)
        self.grid_orders = GridOrderManager(self.client)
        
        # Initialize validator
        self.validator = OrderValidator(self.client)
        
        self.logger.info("Bot initialized successfully")
    
    def display_menu(self):
        """Display the main menu"""
        print("\n" + "="*60)
        print("        BINANCE FUTURES TRADING BOT")
        print("="*60)
        print("BASIC ORDERS:")
        print("1. Market Order")
        print("2. Limit Order")
        print("\nADVANCED ORDERS:")
        print("3. Stop-Limit Order")
        print("4. OCO Order (One-Cancels-Other)")
        print("5. TWAP Order (Time-Weighted Average Price)")
        print("6. Grid Order")
        print("\nUTILITIES:")
        print("7. Check Account Balance")
        print("8. Check Open Orders")
        print("9. Cancel Order")
        print("10. View Order History")
        print("0. Exit")
        print("="*60)
    
    def handle_market_order(self):
        """Handle market order placement"""
        try:
            print("\n--- MARKET ORDER ---")
            symbol = input("Enter symbol (e.g., BTCUSDT): ").upper()
            side = input("Enter side (BUY/SELL): ").upper()
            quantity = input("Enter quantity: ")
            
            # Validate inputs
            if not self.validator.validate_symbol(symbol):
                print("Invalid symbol!")
                return
            
            if not self.validator.validate_side(side):
                print("Invalid side! Use BUY or SELL")
                return
            
            if not self.validator.validate_quantity(quantity):
                print("Invalid quantity!")
                return
            
            quantity = float(quantity)
            
            # Confirm order
            print(f"\nConfirm Market Order:")
            print(f"Symbol: {symbol}")
            print(f"Side: {side}")
            print(f"Quantity: {quantity}")
            
            confirm = input("Execute order? (y/n): ").lower()
            if confirm != 'y':
                print("Order cancelled.")
                return
            
            # Execute order
            result = self.market_orders.place_market_order(symbol, side, quantity)
            if result:
                print(f"Market order executed successfully!")
                print(f"Order ID: {result.get('orderId', 'N/A')}")
            else:
                print("Failed to execute market order")
                
        except Exception as e:
            self.logger.error(f"Error handling market order: {str(e)}")
            print(f"Error: {str(e)}")
    
    def handle_limit_order(self):
        """Handle limit order placement"""
        try:
            print("\n--- LIMIT ORDER ---")
            symbol = input("Enter symbol (e.g., BTCUSDT): ").upper()
            side = input("Enter side (BUY/SELL): ").upper()
            quantity = input("Enter quantity: ")
            price = input("Enter price: ")
            
            # Validate inputs
            if not self.validator.validate_symbol(symbol):
                print("Invalid symbol!")
                return
            
            if not self.validator.validate_side(side):
                print("Invalid side! Use BUY or SELL")
                return
            
            if not self.validator.validate_quantity(quantity):
                print("Invalid quantity!")
                return
            
            if not self.validator.validate_price(price):
                print("Invalid price!")
                return
            
            quantity = float(quantity)
            price = float(price)
            
            # Confirm order
            print(f"\nConfirm Limit Order:")
            print(f"Symbol: {symbol}")
            print(f"Side: {side}")
            print(f"Quantity: {quantity}")
            print(f"Price: {price}")
            
            confirm = input("Execute order? (y/n): ").lower()
            if confirm != 'y':
                print("Order cancelled.")
                return
            
            # Execute order
            result = self.limit_orders.place_limit_order(symbol, side, quantity, price)
            if result:
                print(f"Limit order placed successfully!")
                print(f"Order ID: {result.get('orderId', 'N/A')}")
            else:
                print("Failed to place limit order")
                
        except Exception as e:
            self.logger.error(f"Error handling limit order: {str(e)}")
            print(f"Error: {str(e)}")
    
    def handle_stop_limit_order(self):
        """Handle stop-limit order placement"""
        try:
            print("\n--- STOP-LIMIT ORDER ---")
            symbol = input("Enter symbol (e.g., BTCUSDT): ").upper()
            side = input("Enter side (BUY/SELL): ").upper()
            quantity = input("Enter quantity: ")
            stop_price = input("Enter stop price: ")
            limit_price = input("Enter limit price: ")
            
            # Validate inputs
            if not all([
                self.validator.validate_symbol(symbol),
                self.validator.validate_side(side),
                self.validator.validate_quantity(quantity),
                self.validator.validate_price(stop_price),
                self.validator.validate_price(limit_price)
            ]):
                print("Invalid inputs!")
                return
            
            quantity = float(quantity)
            stop_price = float(stop_price)
            limit_price = float(limit_price)
            
            # Confirm order
            print(f"\nConfirm Stop-Limit Order:")
            print(f"Symbol: {symbol}")
            print(f"Side: {side}")
            print(f"Quantity: {quantity}")
            print(f"Stop Price: {stop_price}")
            print(f"Limit Price: {limit_price}")
            
            confirm = input("Execute order? (y/n): ").lower()
            if confirm != 'y':
                print("Order cancelled.")
                return
            
            # Execute order
            result = self.stop_limit_orders.place_stop_limit_order(symbol, side, quantity, stop_price, limit_price)
            if result:
                print(f"Stop-limit order placed successfully!")
                print(f"Order ID: {result.get('orderId', 'N/A')}")
            else:
                print("Failed to place stop-limit order")
                
        except Exception as e:
            self.logger.error(f"Error handling stop-limit order: {str(e)}")
            print(f"Error: {str(e)}")
    
    def handle_oco_order(self):
        """Handle OCO order placement"""
        try:
            print("\n--- OCO ORDER (One-Cancels-Other) ---")
            symbol = input("Enter symbol (e.g., BTCUSDT): ").upper()
            side = input("Enter side (BUY/SELL): ").upper()
            quantity = input("Enter quantity: ")
            take_profit_price = input("Enter take profit price: ")
            stop_loss_price = input("Enter stop loss price: ")
            
            # Validate inputs
            if not all([
                self.validator.validate_symbol(symbol),
                self.validator.validate_side(side),
                self.validator.validate_quantity(quantity),
                self.validator.validate_price(take_profit_price),
                self.validator.validate_price(stop_loss_price)
            ]):
                print("Invalid inputs!")
                return
            
            quantity = float(quantity)
            take_profit_price = float(take_profit_price)
            stop_loss_price = float(stop_loss_price)
            
            # Confirm order
            print(f"\nConfirm OCO Order:")
            print(f"Symbol: {symbol}")
            print(f"Side: {side}")
            print(f"Quantity: {quantity}")
            print(f"Take Profit Price: {take_profit_price}")
            print(f"Stop Loss Price: {stop_loss_price}")
            
            confirm = input("Execute order? (y/n): ").lower()
            if confirm != 'y':
                print("Order cancelled.")
                return
            
            # Execute order
            result = self.oco_orders.place_oco_order(symbol, side, quantity, take_profit_price, stop_loss_price)
            if result:
                print(f"OCO order placed successfully!")
                print(f"Order List ID: {result.get('orderListId', 'N/A')}")
            else:
                print("Failed to place OCO order")
                
        except Exception as e:
            self.logger.error(f"Error handling OCO order: {str(e)}")
            print(f"Error: {str(e)}")
    
    def handle_twap_order(self):
        """Handle TWAP order placement"""
        try:
            print("\n--- TWAP ORDER (Time-Weighted Average Price) ---")
            symbol = input("Enter symbol (e.g., BTCUSDT): ").upper()
            side = input("Enter side (BUY/SELL): ").upper()
            total_quantity = input("Enter total quantity: ")
            duration_minutes = input("Enter duration in minutes: ")
            interval_seconds = input("Enter interval between orders (seconds): ")
            
            # Validate inputs
            if not all([
                self.validator.validate_symbol(symbol),
                self.validator.validate_side(side),
                self.validator.validate_quantity(total_quantity)
            ]):
                print("Invalid inputs!")
                return
            
            total_quantity = float(total_quantity)
            duration_minutes = int(duration_minutes)
            interval_seconds = int(interval_seconds)
            
            # Confirm order
            print(f"\nConfirm TWAP Order:")
            print(f"Symbol: {symbol}")
            print(f"Side: {side}")
            print(f"Total Quantity: {total_quantity}")
            print(f"Duration: {duration_minutes} minutes")
            print(f"Interval: {interval_seconds} seconds")
            
            confirm = input("Execute order? (y/n): ").lower()
            if confirm != 'y':
                print("Order cancelled.")
                return
            
            # Execute order
            result = self.twap_orders.place_twap_order(symbol, side, total_quantity, duration_minutes, interval_seconds)
            if result:
                print(f"TWAP order started successfully!")
                print(f"Job ID: {result.get('job_id', 'N/A')}")
            else:
                print("Failed to start TWAP order")
                
        except Exception as e:
            self.logger.error(f"Error handling TWAP order: {str(e)}")
            print(f"Error: {str(e)}")
    
    def handle_grid_order(self):
        """Handle grid order placement"""
        try:
            print("\n--- GRID ORDER ---")
            symbol = input("Enter symbol (e.g., BTCUSDT): ").upper()
            grid_count = input("Enter number of grid levels: ")
            price_range_min = input("Enter minimum price: ")
            price_range_max = input("Enter maximum price: ")
            total_quantity = input("Enter total quantity: ")
            
            # Validate inputs
            if not all([
                self.validator.validate_symbol(symbol),
                self.validator.validate_quantity(total_quantity),
                self.validator.validate_price(price_range_min),
                self.validator.validate_price(price_range_max)
            ]):
                print("Invalid inputs!")
                return
            
            grid_count = int(grid_count)
            price_range_min = float(price_range_min)
            price_range_max = float(price_range_max)
            total_quantity = float(total_quantity)
            
            # Confirm order
            print(f"\nConfirm Grid Order:")
            print(f"Symbol: {symbol}")
            print(f"Grid Levels: {grid_count}")
            print(f"Price Range: {price_range_min} - {price_range_max}")
            print(f"Total Quantity: {total_quantity}")
            
            confirm = input("Execute order? (y/n): ").lower()
            if confirm != 'y':
                print("Order cancelled.")
                return
            
            # Execute order
            result = self.grid_orders.place_grid_order(symbol, grid_count, price_range_min, price_range_max, total_quantity)
            if result:
                print(f"Grid order placed successfully!")
                print(f"Orders placed: {len(result.get('orders', []))}")
            else:
                print("Failed to place grid order")
                
        except Exception as e:
            self.logger.error(f"Error handling grid order: {str(e)}")
            print(f"Error: {str(e)}")
    
    def check_account_balance(self):
        """Check account balance"""
        try:
            print("\n--- ACCOUNT BALANCE ---")
            balance = self.client.get_account_balance()
            if balance:
                print(f"Account Balance:")
                for asset in balance:
                    if float(asset['balance']) > 0:
                        print(f"{asset['asset']}: {asset['balance']}")
            else:
                print("Failed to retrieve account balance")
        except Exception as e:
            self.logger.error(f"Error checking account balance: {str(e)}")
            print(f"Error: {str(e)}")
    
    def check_open_orders(self):
        """Check open orders"""
        try:
            print("\n--- OPEN ORDERS ---")
            symbol = input("Enter symbol (leave blank for all): ").upper()
            
            orders = self.client.get_open_orders(symbol if symbol else None)
            if orders:
                print(f"Open Orders:")
                for order in orders:
                    print(f"ID: {order['orderId']}, Symbol: {order['symbol']}, "
                          f"Side: {order['side']}, Quantity: {order['origQty']}, "
                          f"Price: {order['price']}, Status: {order['status']}")
            else:
                print("No open orders found")
        except Exception as e:
            self.logger.error(f"Error checking open orders: {str(e)}")
            print(f"Error: {str(e)}")
    
    def cancel_order(self):
        """Cancel an order"""
        try:
            print("\n--- CANCEL ORDER ---")
            symbol = input("Enter symbol: ").upper()
            order_id = input("Enter order ID: ")
            
            if not self.validator.validate_symbol(symbol):
                print("Invalid symbol!")
                return
            
            # Confirm cancellation
            confirm = input(f"Cancel order {order_id} for {symbol}? (y/n): ").lower()
            if confirm != 'y':
                print("Cancellation aborted.")
                return
            
            result = self.client.cancel_order(symbol, order_id)
            if result:
                print(f"Order {order_id} cancelled successfully!")
            else:
                print("Failed to cancel order")
                
        except Exception as e:
            self.logger.error(f"Error cancelling order: {str(e)}")
            print(f"Error: {str(e)}")
    
    def view_order_history(self):
        """View order history"""
        try:
            print("\n--- ORDER HISTORY ---")
            symbol = input("Enter symbol: ").upper()
            
            if not self.validator.validate_symbol(symbol):
                print("Invalid symbol!")
                return
            
            orders = self.client.get_order_history(symbol)
            if orders:
                print(f"Order History for {symbol}:")
                for order in orders[-10:]:  # Show last 10 orders
                    print(f"ID: {order['orderId']}, Side: {order['side']}, "
                          f"Quantity: {order['origQty']}, Price: {order['price']}, "
                          f"Status: {order['status']}, Time: {order['time']}")
            else:
                print("No order history found")
                
        except Exception as e:
            self.logger.error(f"Error viewing order history: {str(e)}")
            print(f"Error: {str(e)}")
    
    def run(self):
        """Main bot loop"""
        self.logger.info("Starting bot main loop")
        
        while True:
            try:
                self.display_menu()
                choice = input("\nEnter your choice (0-10): ").strip()
                
                if choice == '0':
                    print("Exiting bot...")
                    self.logger.info("Bot shutdown requested")
                    break
                elif choice == '1':
                    self.handle_market_order()
                elif choice == '2':
                    self.handle_limit_order()
                elif choice == '3':
                    self.handle_stop_limit_order()
                elif choice == '4':
                    self.handle_oco_order()
                elif choice == '5':
                    self.handle_twap_order()
                elif choice == '6':
                    self.handle_grid_order()
                elif choice == '7':
                    self.check_account_balance()
                elif choice == '8':
                    self.check_open_orders()
                elif choice == '9':
                    self.cancel_order()
                elif choice == '10':
                    self.view_order_history()
                else:
                    print("Invalid choice! Please try again.")
                    
            except KeyboardInterrupt:
                print("\nBot interrupted by user")
                self.logger.info("Bot interrupted by user")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error in main loop: {str(e)}")
                print(f"Unexpected error: {str(e)}")
                continue

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Binance Futures Trading Bot')
    parser.add_argument('--testnet', action='store_true', help='Use Binance testnet')
    parser.add_argument('--api-key', type=str, help='Binance API key')
    parser.add_argument('--secret-key', type=str, help='Binance secret key')
    
    args = parser.parse_args()
    
    # Get API credentials
    api_key = args.api_key or os.environ.get('BINANCE_API_KEY')
    secret_key = args.secret_key or os.environ.get('BINANCE_SECRET_KEY')
    
    if not api_key or not secret_key:
        print("Error: API key and secret key are required!")
        print("Provide them via command line arguments or environment variables.")
        return
    
    # Create and run bot
    bot = BinanceFuturesBot(F8wmuzN5RQiQXZdLUh1rlzQGR2YDrUJuxHNblQS1fwbeblElqHjQxylg7CQSu6NL, Y5sg3jC1K8GYsP7vAgambxRzrNCqfbNa8HppuFxW8Q17TUJAASnF34l5KiJBRxyy, args.testnet)
    bot.run()

if __name__ == "__main__":
    main()
