"""
Market Order Manager for Binance Futures
Handles market order placement and execution
"""

from typing import Optional, Dict, Any
from logger import setup_logger, log_order_action
import time

class MarketOrderManager:
    """
    Manages market order placement and execution
    """
    
    def __init__(self, binance_client):
        """Initialize market order manager"""
        self.client = binance_client
        self.logger = setup_logger('MarketOrderManager')
        self.logger.info("Market Order Manager initialized")
    
    def place_market_order(self, symbol: str, side: str, quantity: float) -> Optional[Dict[str, Any]]:
        """
        Place a market order
        
        Args:
            symbol: Trading symbol (e.g., BTCUSDT)
            side: Order side (BUY/SELL)
            quantity: Order quantity
            
        Returns:
            Dict containing order result or None if failed
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Placing market order: {symbol} {side} {quantity}")
            
            # Log the order action
            log_order_action(
                self.logger, 
                'PLACE_MARKET', 
                symbol, 
                side, 
                quantity
            )
            
            # Place the order
            result = self.client.place_order(
                symbol=symbol,
                side=side,
                order_type='MARKET',
                quantity=quantity
            )
            
            execution_time = time.time() - start_time
            
            if result:
                order_id = result.get('orderId')
                self.logger.info(f"Market order placed successfully: {order_id} in {execution_time:.3f}s")
                
                # Log successful order placement
                log_order_action(
                    self.logger,
                    'PLACED_MARKET',
                    symbol,
                    side,
                    quantity,
                    order_id=str(order_id)
                )
                
                return result
            else:
                self.logger.error(f"Failed to place market order: {symbol} {side} {quantity}")
                
                # Log failed order placement
                log_order_action(
                    self.logger,
                    'FAILED_MARKET',
                    symbol,
                    side,
                    quantity,
                    error="Order placement failed"
                )
                
                return None
                
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            self.logger.error(f"Error placing market order: {error_msg}")
            
            # Log error
            log_order_action(
                self.logger,
                'ERROR_MARKET',
                symbol,
                side,
                quantity,
                error=error_msg
            )
            
            return None
    
    def place_market_buy(self, symbol: str, quantity: float) -> Optional[Dict[str, Any]]:
        """
        Place a market buy order
        
        Args:
            symbol: Trading symbol
            quantity: Quantity to buy
            
        Returns:
            Order result or None if failed
        """
        return self.place_market_order(symbol, 'BUY', quantity)
    
    def place_market_sell(self, symbol: str, quantity: float) -> Optional[Dict[str, Any]]:
        """
        Place a market sell order
        
        Args:
            symbol: Trading symbol
            quantity: Quantity to sell
            
        Returns:
            Order result or None if failed
        """
        return self.place_market_order(symbol, 'SELL', quantity)
    
    def place_market_order_quote_quantity(self, symbol: str, side: str, quote_quantity: float) -> Optional[Dict[str, Any]]:
        """
        Place a market order with quote quantity (USDT amount)
        
        Args:
            symbol: Trading symbol
            side: Order side (BUY/SELL)
            quote_quantity: Quote asset quantity (e.g., USDT amount)
            
        Returns:
            Order result or None if failed
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Placing market order by quote: {symbol} {side} {quote_quantity} USDT")
            
            # Log the order action
            log_order_action(
                self.logger,
                'PLACE_MARKET_QUOTE',
                symbol,
                side,
                quote_quantity
            )
            
            # Place the order with quote quantity
            result = self.client.place_order(
                symbol=symbol,
                side=side,
                order_type='MARKET',
                quoteOrderQty=quote_quantity
            )
            
            execution_time = time.time() - start_time
            
            if result:
                order_id = result.get('orderId')
                executed_qty = result.get('executedQty', 0)
                self.logger.info(f"Market order by quote placed successfully: {order_id}, executed qty: {executed_qty} in {execution_time:.3f}s")
                
                # Log successful order placement
                log_order_action(
                    self.logger,
                    'PLACED_MARKET_QUOTE',
                    symbol,
                    side,
                    executed_qty,
                    order_id=str(order_id)
                )
                
                return result
            else:
                self.logger.error(f"Failed to place market order by quote: {symbol} {side} {quote_quantity}")
                
                # Log failed order placement
                log_order_action(
                    self.logger,
                    'FAILED_MARKET_QUOTE',
                    symbol,
                    side,
                    quote_quantity,
                    error="Order placement failed"
                )
                
                return None
                
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            self.logger.error(f"Error placing market order by quote: {error_msg}")
            
            # Log error
            log_order_action(
                self.logger,
                'ERROR_MARKET_QUOTE',
                symbol,
                side,
                quote_quantity,
                error=error_msg
            )
            
            return None
    
    def get_estimated_price(self, symbol: str) -> Optional[float]:
        """
        Get estimated price for market order
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Estimated price or None if failed
        """
        try:
            ticker = self.client.get_ticker_price(symbol)
            if ticker:
                price = float(ticker.get('price', 0))
                self.logger.debug(f"Estimated price for {symbol}: {price}")
                return price
            else:
                self.logger.error(f"Failed to get ticker price for {symbol}")
                return None
        except Exception as e:
            self.logger.error(f"Error getting estimated price for {symbol}: {str(e)}")
            return None
    
    def calculate_market_order_cost(self, symbol: str, side: str, quantity: float) -> Optional[Dict[str, float]]:
        """
        Calculate estimated cost for a market order
        
        Args:
            symbol: Trading symbol
            side: Order side
            quantity: Order quantity
            
        Returns:
            Dict with cost estimates or None if failed
        """
        try:
            estimated_price = self.get_estimated_price(symbol)
            if estimated_price is None:
                return None
            
            # Calculate estimated cost
            estimated_cost = quantity * estimated_price
            
            # Add estimated slippage (0.1% for market orders)
            slippage_factor = 1.001 if side.upper() == 'BUY' else 0.999
            estimated_cost_with_slippage = estimated_cost * slippage_factor
            
            result = {
                'estimated_price': estimated_price,
                'quantity': quantity,
                'estimated_cost': estimated_cost,
                'estimated_cost_with_slippage': estimated_cost_with_slippage,
                'estimated_slippage': abs(estimated_cost_with_slippage - estimated_cost)
            }
            
            self.logger.debug(f"Market order cost estimate for {symbol}: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error calculating market order cost: {str(e)}")
            return None
    
    def validate_balance_for_order(self, symbol: str, side: str, quantity: float) -> bool:
        """
        Validate if account has sufficient balance for the order
        
        Args:
            symbol: Trading symbol
            side: Order side
            quantity: Order quantity
            
        Returns:
            True if sufficient balance, False otherwise
        """
        try:
            # Get account balance
            balance = self.client.get_account_balance()
            if not balance:
                self.logger.error("Failed to get account balance")
                return False
            
            # Extract base and quote assets from symbol
            # Assuming USDT pairs (e.g., BTCUSDT)
            if symbol.endswith('USDT'):
                base_asset = symbol[:-4]  # Remove 'USDT'
                quote_asset = 'USDT'
            else:
                # For other pairs, this is a simplification
                self.logger.warning(f"Non-USDT pair detected: {symbol}, balance validation may be inaccurate")
                return True
            
            # Find relevant balances
            base_balance = 0
            quote_balance = 0
            
            for asset in balance:
                if asset['asset'] == base_asset:
                    base_balance = float(asset['balance'])
                elif asset['asset'] == quote_asset:
                    quote_balance = float(asset['balance'])
            
            if side.upper() == 'SELL':
                # For sell orders, check base asset balance
                if base_balance >= quantity:
                    self.logger.debug(f"Sufficient {base_asset} balance: {base_balance} >= {quantity}")
                    return True
                else:
                    self.logger.error(f"Insufficient {base_asset} balance: {base_balance} < {quantity}")
                    return False
            else:  # BUY
                # For buy orders, estimate cost and check quote asset balance
                cost_estimate = self.calculate_market_order_cost(symbol, side, quantity)
                if cost_estimate:
                    required_quote = cost_estimate['estimated_cost_with_slippage']
                    if quote_balance >= required_quote:
                        self.logger.debug(f"Sufficient {quote_asset} balance: {quote_balance} >= {required_quote}")
                        return True
                    else:
                        self.logger.error(f"Insufficient {quote_asset} balance: {quote_balance} < {required_quote}")
                        return False
                else:
                    self.logger.warning("Could not estimate order cost, skipping balance validation")
                    return True
                    
        except Exception as e:
            self.logger.error(f"Error validating balance: {str(e)}")
            return False
    
    def place_market_order_with_validation(self, symbol: str, side: str, quantity: float) -> Optional[Dict[str, Any]]:
        """
        Place market order with comprehensive validation
        
        Args:
            symbol: Trading symbol
            side: Order side
            quantity: Order quantity
            
        Returns:
            Order result or None if failed
        """
        try:
            # Validate balance
            if not self.validate_balance_for_order(symbol, side, quantity):
                self.logger.error("Balance validation failed")
                return None
            
            # Get cost estimate
            cost_estimate = self.calculate_market_order_cost(symbol, side, quantity)
            if cost_estimate:
                self.logger.info(f"Order cost estimate: {cost_estimate}")
            
            # Place the order
            return self.place_market_order(symbol, side, quantity)
            
        except Exception as e:
            self.logger.error(f"Error in validated market order placement: {str(e)}")
            return None
