"""
Stop-Limit Order Manager for Binance Futures
Handles stop-limit order placement and management
"""

from typing import Optional, Dict, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from logger import setup_logger, log_order_action
import time

class StopLimitOrderManager:
    """
    Manages stop-limit order placement and execution
    """
    
    def __init__(self, binance_client):
        """Initialize stop-limit order manager"""
        self.client = binance_client
        self.logger = setup_logger('StopLimitOrderManager')
        self.logger.info("Stop-Limit Order Manager initialized")
    
    def place_stop_limit_order(self, symbol: str, side: str, quantity: float, 
                              stop_price: float, limit_price: float) -> Optional[Dict[str, Any]]:
        """
        Place a stop-limit order
        
        Args:
            symbol: Trading symbol (e.g., BTCUSDT)
            side: Order side (BUY/SELL)
            quantity: Order quantity
            stop_price: Stop price (trigger price)
            limit_price: Limit price (execution price)
            
        Returns:
            Dict containing order result or None if failed
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Placing stop-limit order: {symbol} {side} {quantity} stop@{stop_price} limit@{limit_price}")
            
            # Log the order action
            log_order_action(
                self.logger,
                'PLACE_STOP_LIMIT',
                symbol,
                side,
                quantity,
                price=limit_price
            )
            
            # Place the order
            result = self.client.place_order(
                symbol=symbol,
                side=side,
                order_type='STOP',
                quantity=quantity,
                price=limit_price,
                stop_price=stop_price,
                timeInForce='GTC'
            )
            
            execution_time = time.time() - start_time
            
            if result:
                order_id = result.get('orderId')
                self.logger.info(f"Stop-limit order placed successfully: {order_id} in {execution_time:.3f}s")
                
                # Log successful order placement
                log_order_action(
                    self.logger,
                    'PLACED_STOP_LIMIT',
                    symbol,
                    side,
                    quantity,
                    price=limit_price,
                    order_id=str(order_id)
                )
                
                return result
            else:
                self.logger.error(f"Failed to place stop-limit order: {symbol} {side} {quantity}")
                
                # Log failed order placement
                log_order_action(
                    self.logger,
                    'FAILED_STOP_LIMIT',
                    symbol,
                    side,
                    quantity,
                    price=limit_price,
                    error="Order placement failed"
                )
                
                return None
                
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            self.logger.error(f"Error placing stop-limit order: {error_msg}")
            
            # Log error
            log_order_action(
                self.logger,
                'ERROR_STOP_LIMIT',
                symbol,
                side,
                quantity,
                price=limit_price,
                error=error_msg
            )
            
            return None
    
    def place_stop_market_order(self, symbol: str, side: str, quantity: float, 
                               stop_price: float) -> Optional[Dict[str, Any]]:
        """
        Place a stop-market order (market order triggered at stop price)
        
        Args:
            symbol: Trading symbol
            side: Order side
            quantity: Order quantity
            stop_price: Stop price (trigger price)
            
        Returns:
            Order result or None if failed
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Placing stop-market order: {symbol} {side} {quantity} stop@{stop_price}")
            
            # Log the order action
            log_order_action(
                self.logger,
                'PLACE_STOP_MARKET',
                symbol,
                side,
                quantity
            )
            
            # Place the order
            result = self.client.place_order(
                symbol=symbol,
                side=side,
                order_type='STOP_MARKET',
                quantity=quantity,
                stop_price=stop_price
            )
            
            execution_time = time.time() - start_time
            
            if result:
                order_id = result.get('orderId')
                self.logger.info(f"Stop-market order placed successfully: {order_id} in {execution_time:.3f}s")
                
                # Log successful order placement
                log_order_action(
                    self.logger,
                    'PLACED_STOP_MARKET',
                    symbol,
                    side,
                    quantity,
                    order_id=str(order_id)
                )
                
                return result
            else:
                self.logger.error(f"Failed to place stop-market order")
                return None
                
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Error placing stop-market order: {error_msg}")
            return None
    
    def place_take_profit_order(self, symbol: str, side: str, quantity: float, 
                               take_profit_price: float) -> Optional[Dict[str, Any]]:
        """
        Place a take-profit order
        
        Args:
            symbol: Trading symbol
            side: Order side
            quantity: Order quantity
            take_profit_price: Take profit price
            
        Returns:
            Order result or None if failed
        """
        try:
            self.logger.info(f"Placing take-profit order: {symbol} {side} {quantity} TP@{take_profit_price}")
            
            # Log the order action
            log_order_action(
                self.logger,
                'PLACE_TAKE_PROFIT',
                symbol,
                side,
                quantity,
                price=take_profit_price
            )
            
            # Place the order
            result = self.client.place_order(
                symbol=symbol,
                side=side,
                order_type='TAKE_PROFIT',
                quantity=quantity,
                price=take_profit_price,
                stop_price=take_profit_price,
                timeInForce='GTC'
            )
            
            if result:
                order_id = result.get('orderId')
                self.logger.info(f"Take-profit order placed successfully: {order_id}")
                
                # Log successful order placement
                log_order_action(
                    self.logger,
                    'PLACED_TAKE_PROFIT',
                    symbol,
                    side,
                    quantity,
                    price=take_profit_price,
                    order_id=str(order_id)
                )
                
                return result
            else:
                self.logger.error(f"Failed to place take-profit order")
                return None
                
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Error placing take-profit order: {error_msg}")
            
            # Log error
            log_order_action(
                self.logger,
                'ERROR_TAKE_PROFIT',
                symbol,
                side,
                quantity,
                price=take_profit_price,
                error=error_msg
            )
            
            return None
    
    def place_trailing_stop_order(self, symbol: str, side: str, quantity: float, 
                                 callback_rate: float) -> Optional[Dict[str, Any]]:
        """
        Place a trailing stop order
        
        Args:
            symbol: Trading symbol
            side: Order side
            quantity: Order quantity
            callback_rate: Callback rate in percentage (e.g., 1.0 for 1%)
            
        Returns:
            Order result or None if failed
        """
        try:
            self.logger.info(f"Placing trailing stop order: {symbol} {side} {quantity} callback={callback_rate}%")
            
            # Log the order action
            log_order_action(
                self.logger,
                'PLACE_TRAILING_STOP',
                symbol,
                side,
                quantity
            )
            
            # Place the order
            result = self.client.place_order(
                symbol=symbol,
                side=side,
                order_type='TRAILING_STOP_MARKET',
                quantity=quantity,
                callbackRate=callback_rate
            )
            
            if result:
                order_id = result.get('orderId')
                self.logger.info(f"Trailing stop order placed successfully: {order_id}")
                
                # Log successful order placement
                log_order_action(
                    self.logger,
                    'PLACED_TRAILING_STOP',
                    symbol,
                    side,
                    quantity,
                    order_id=str(order_id)
                )
                
                return result
            else:
                self.logger.error(f"Failed to place trailing stop order")
                return None
                
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Error placing trailing stop order: {error_msg}")
            
            # Log error
            log_order_action(
                self.logger,
                'ERROR_TRAILING_STOP',
                symbol,
                side,
                quantity,
                error=error_msg
            )
            
            return None
    
    def get_current_market_price(self, symbol: str) -> Optional[float]:
        """
        Get current market price for the symbol
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Current price or None if failed
        """
        try:
            ticker = self.client.get_ticker_price(symbol)
            if ticker:
                price = float(ticker.get('price', 0))
                self.logger.debug(f"Current market price for {symbol}: {price}")
                return price
            else:
                self.logger.error(f"Failed to get market price for {symbol}")
                return None
        except Exception as e:
            self.logger.error(f"Error getting market price for {symbol}: {str(e)}")
            return None
    
    def validate_stop_limit_prices(self, symbol: str, side: str, stop_price: float, 
                                  limit_price: float) -> bool:
        """
        Validate stop-limit order prices
        
        Args:
            symbol: Trading symbol
            side: Order side
            stop_price: Stop price
            limit_price: Limit price
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Get current market price
            market_price = self.get_current_market_price(symbol)
            if market_price is None:
                self.logger.warning("Could not get market price for validation")
                return True  # Allow order if we can't validate
            
            if side.upper() == 'BUY':
                # For BUY stop-limit:
                # - Stop price should be above current market price
                # - Limit price should be >= stop price
                if stop_price <= market_price:
                    self.logger.error(f"BUY stop price {stop_price} should be above market price {market_price}")
                    return False
                
                if limit_price < stop_price:
                    self.logger.error(f"BUY limit price {limit_price} should be >= stop price {stop_price}")
                    return False
                    
            else:  # SELL
                # For SELL stop-limit:
                # - Stop price should be below current market price
                # - Limit price should be <= stop price
                if stop_price >= market_price:
                    self.logger.error(f"SELL stop price {stop_price} should be below market price {market_price}")
                    return False
                
                if limit_price > stop_price:
                    self.logger.error(f"SELL limit price {limit_price} should be <= stop price {stop_price}")
                    return False
            
            self.logger.info(f"Stop-limit price validation passed for {side} order")
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating stop-limit prices: {str(e)}")
            return False
    
    def place_stop_limit_with_validation(self, symbol: str, side: str, quantity: float,
                                        stop_price: float, limit_price: float) -> Optional[Dict[str, Any]]:
        """
        Place stop-limit order with price validation
        
        Args:
            symbol: Trading symbol
            side: Order side
            quantity: Order quantity
            stop_price: Stop price
            limit_price: Limit price
            
        Returns:
            Order result or None if failed
        """
        try:
            # Validate prices
            if not self.validate_stop_limit_prices(symbol, side, stop_price, limit_price):
                self.logger.error("Stop-limit price validation failed")
                return None
            
            # Place the order
            return self.place_stop_limit_order(symbol, side, quantity, stop_price, limit_price)
            
        except Exception as e:
            self.logger.error(f"Error in validated stop-limit order placement: {str(e)}")
            return None
    
    def calculate_stop_loss_price(self, symbol: str, side: str, entry_price: float, 
                                 stop_loss_percentage: float) -> Optional[float]:
        """
        Calculate stop loss price based on percentage
        
        Args:
            symbol: Trading symbol
            side: Order side
            entry_price: Entry price
            stop_loss_percentage: Stop loss percentage (e.g., 2.0 for 2%)
            
        Returns:
            Stop loss price or None if failed
        """
        try:
            if side.upper() == 'BUY':
                # For long position, stop loss is below entry price
                stop_loss_price = entry_price * (1 - stop_loss_percentage / 100)
            else:  # SELL
                # For short position, stop loss is above entry price
                stop_loss_price = entry_price * (1 + stop_loss_percentage / 100)
            
            self.logger.info(f"Calculated stop loss price for {side} at {entry_price}: {stop_loss_price} ({stop_loss_percentage}%)")
            return stop_loss_price
            
        except Exception as e:
            self.logger.error(f"Error calculating stop loss price: {str(e)}")
            return None
    
    def calculate_take_profit_price(self, symbol: str, side: str, entry_price: float, 
                                   take_profit_percentage: float) -> Optional[float]:
        """
        Calculate take profit price based on percentage
        
        Args:
            symbol: Trading symbol
            side: Order side
            entry_price: Entry price
            take_profit_percentage: Take profit percentage (e.g., 5.0 for 5%)
            
        Returns:
            Take profit price or None if failed
        """
        try:
            if side.upper() == 'BUY':
                # For long position, take profit is above entry price
                take_profit_price = entry_price * (1 + take_profit_percentage / 100)
            else:  # SELL
                # For short position, take profit is below entry price
                take_profit_price = entry_price * (1 - take_profit_percentage / 100)
            
            self.logger.info(f"Calculated take profit price for {side} at {entry_price}: {take_profit_price} ({take_profit_percentage}%)")
            return take_profit_price
            
        except Exception as e:
            self.logger.error(f"Error calculating take profit price: {str(e)}")
            return None
    
    def place_position_protection(self, symbol: str, side: str, quantity: float, 
                                 entry_price: float, stop_loss_pct: float, 
                                 take_profit_pct: float) -> Optional[Dict[str, Any]]:
        """
        Place stop loss and take profit orders for a position
        
        Args:
            symbol: Trading symbol
            side: Position side (BUY for long, SELL for short)
            quantity: Position quantity
            entry_price: Entry price
            stop_loss_pct: Stop loss percentage
            take_profit_pct: Take profit percentage
            
        Returns:
            Dict with both order results or None if failed
        """
        try:
            self.logger.info(f"Placing position protection: {symbol} {side} SL={stop_loss_pct}% TP={take_profit_pct}%")
            
            # Calculate prices
            stop_loss_price = self.calculate_stop_loss_price(symbol, side, entry_price, stop_loss_pct)
            take_profit_price = self.calculate_take_profit_price(symbol, side, entry_price, take_profit_pct)
            
            if stop_loss_price is None or take_profit_price is None:
                self.logger.error("Failed to calculate protection prices")
                return None
            
            # Determine exit side (opposite of position)
            exit_side = 'SELL' if side.upper() == 'BUY' else 'BUY'
            
            # Place stop loss order
            stop_loss_order = self.place_stop_market_order(symbol, exit_side, quantity, stop_loss_price)
            
            # Place take profit order
            take_profit_order = self.place_take_profit_order(symbol, exit_side, quantity, take_profit_price)
            
            result = {
                'stop_loss_order': stop_loss_order,
                'take_profit_order': take_profit_order,
                'stop_loss_price': stop_loss_price,
                'take_profit_price': take_profit_price,
                'status': 'complete' if (stop_loss_order and take_profit_order) else 'partial'
            }
            
            self.logger.info(f"Position protection placed: SL={stop_loss_order.get('orderId') if stop_loss_order else 'failed'}, TP={take_profit_order.get('orderId') if take_profit_order else 'failed'}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error placing position protection: {str(e)}")
            return None
