"""
Limit Order Manager for Binance Futures
Handles limit order placement and management
"""

from typing import Optional, Dict, Any, List
from logger import setup_logger, log_order_action
import time

class LimitOrderManager:
    """
    Manages limit order placement and execution
    """
    
    def __init__(self, binance_client):
        """Initialize limit order manager"""
        self.client = binance_client
        self.logger = setup_logger('LimitOrderManager')
        self.logger.info("Limit Order Manager initialized")
    
    def place_limit_order(self, symbol: str, side: str, quantity: float, price: float, 
                         time_in_force: str = 'GTC') -> Optional[Dict[str, Any]]:
        """
        Place a limit order
        
        Args:
            symbol: Trading symbol (e.g., BTCUSDT)
            side: Order side (BUY/SELL)
            quantity: Order quantity
            price: Order price
            time_in_force: Time in force (GTC, IOC, FOK)
            
        Returns:
            Dict containing order result or None if failed
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Placing limit order: {symbol} {side} {quantity} @ {price}")
            
            # Log the order action
            log_order_action(
                self.logger,
                'PLACE_LIMIT',
                symbol,
                side,
                quantity,
                price=price
            )
            
            # Place the order
            result = self.client.place_order(
                symbol=symbol,
                side=side,
                order_type='LIMIT',
                quantity=quantity,
                price=price,
                timeInForce=time_in_force
            )
            
            execution_time = time.time() - start_time
            
            if result:
                order_id = result.get('orderId')
                self.logger.info(f"Limit order placed successfully: {order_id} in {execution_time:.3f}s")
                
                # Log successful order placement
                log_order_action(
                    self.logger,
                    'PLACED_LIMIT',
                    symbol,
                    side,
                    quantity,
                    price=price,
                    order_id=str(order_id)
                )
                
                return result
            else:
                self.logger.error(f"Failed to place limit order: {symbol} {side} {quantity} @ {price}")
                
                # Log failed order placement
                log_order_action(
                    self.logger,
                    'FAILED_LIMIT',
                    symbol,
                    side,
                    quantity,
                    price=price,
                    error="Order placement failed"
                )
                
                return None
                
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            self.logger.error(f"Error placing limit order: {error_msg}")
            
            # Log error
            log_order_action(
                self.logger,
                'ERROR_LIMIT',
                symbol,
                side,
                quantity,
                price=price,
                error=error_msg
            )
            
            return None
    
    def place_limit_buy(self, symbol: str, quantity: float, price: float) -> Optional[Dict[str, Any]]:
        """
        Place a limit buy order
        
        Args:
            symbol: Trading symbol
            quantity: Quantity to buy
            price: Buy price
            
        Returns:
            Order result or None if failed
        """
        return self.place_limit_order(symbol, 'BUY', quantity, price)
    
    def place_limit_sell(self, symbol: str, quantity: float, price: float) -> Optional[Dict[str, Any]]:
        """
        Place a limit sell order
        
        Args:
            symbol: Trading symbol
            quantity: Quantity to sell
            price: Sell price
            
        Returns:
            Order result or None if failed
        """
        return self.place_limit_order(symbol, 'SELL', quantity, price)
    
    def place_post_only_order(self, symbol: str, side: str, quantity: float, price: float) -> Optional[Dict[str, Any]]:
        """
        Place a post-only limit order (maker only)
        
        Args:
            symbol: Trading symbol
            side: Order side
            quantity: Order quantity
            price: Order price
            
        Returns:
            Order result or None if failed
        """
        try:
            self.logger.info(f"Placing post-only order: {symbol} {side} {quantity} @ {price}")
            
            # Log the order action
            log_order_action(
                self.logger,
                'PLACE_POST_ONLY',
                symbol,
                side,
                quantity,
                price=price
            )
            
            # Place the order with GTX (Good Till Crossing)
            result = self.client.place_order(
                symbol=symbol,
                side=side,
                order_type='LIMIT',
                quantity=quantity,
                price=price,
                timeInForce='GTX'  # Good Till Crossing - post only
            )
            
            if result:
                order_id = result.get('orderId')
                self.logger.info(f"Post-only order placed successfully: {order_id}")
                
                # Log successful order placement
                log_order_action(
                    self.logger,
                    'PLACED_POST_ONLY',
                    symbol,
                    side,
                    quantity,
                    price=price,
                    order_id=str(order_id)
                )
                
                return result
            else:
                self.logger.error(f"Failed to place post-only order")
                return None
                
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Error placing post-only order: {error_msg}")
            
            # Log error
            log_order_action(
                self.logger,
                'ERROR_POST_ONLY',
                symbol,
                side,
                quantity,
                price=price,
                error=error_msg
            )
            
            return None
    
    def modify_limit_order(self, symbol: str, order_id: str, quantity: float = None, 
                          price: float = None) -> Optional[Dict[str, Any]]:
        """
        Modify an existing limit order
        Note: Binance doesn't support direct order modification, so we cancel and replace
        
        Args:
            symbol: Trading symbol
            order_id: Order ID to modify
            quantity: New quantity (optional)
            price: New price (optional)
            
        Returns:
            New order result or None if failed
        """
        try:
            # First, get the current order details
            current_order = self.client.get_order_status(symbol, order_id)
            if not current_order:
                self.logger.error(f"Could not retrieve order {order_id} for modification")
                return None
            
            # Cancel the existing order
            cancel_result = self.client.cancel_order(symbol, order_id)
            if not cancel_result:
                self.logger.error(f"Failed to cancel order {order_id} for modification")
                return None
            
            # Prepare new order parameters
            new_quantity = quantity if quantity is not None else float(current_order['origQty'])
            new_price = price if price is not None else float(current_order['price'])
            side = current_order['side']
            
            self.logger.info(f"Modifying order {order_id}: new qty={new_quantity}, new price={new_price}")
            
            # Place the new order
            new_order = self.place_limit_order(symbol, side, new_quantity, new_price)
            
            if new_order:
                self.logger.info(f"Order modified successfully: old={order_id}, new={new_order.get('orderId')}")
                
                # Log the modification
                log_order_action(
                    self.logger,
                    'MODIFIED_LIMIT',
                    symbol,
                    side,
                    new_quantity,
                    price=new_price,
                    order_id=str(new_order.get('orderId'))
                )
                
                return new_order
            else:
                self.logger.error(f"Failed to place replacement order after cancelling {order_id}")
                return None
                
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Error modifying limit order: {error_msg}")
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
    
    def calculate_limit_order_distance(self, symbol: str, price: float) -> Optional[Dict[str, float]]:
        """
        Calculate distance of limit order from current market price
        
        Args:
            symbol: Trading symbol
            price: Limit order price
            
        Returns:
            Dict with distance calculations or None if failed
        """
        try:
            market_price = self.get_current_market_price(symbol)
            if market_price is None:
                return None
            
            absolute_distance = abs(price - market_price)
            percentage_distance = (absolute_distance / market_price) * 100
            
            # Determine if order is above or below market
            if price > market_price:
                direction = "above"
            elif price < market_price:
                direction = "below"
            else:
                direction = "at"
            
            result = {
                'market_price': market_price,
                'limit_price': price,
                'absolute_distance': absolute_distance,
                'percentage_distance': percentage_distance,
                'direction': direction
            }
            
            self.logger.debug(f"Limit order distance for {symbol}: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error calculating limit order distance: {str(e)}")
            return None
    
    def place_limit_order_with_distance_check(self, symbol: str, side: str, quantity: float, 
                                            price: float, max_distance_pct: float = 5.0) -> Optional[Dict[str, Any]]:
        """
        Place limit order with distance check from market price
        
        Args:
            symbol: Trading symbol
            side: Order side
            quantity: Order quantity
            price: Order price
            max_distance_pct: Maximum allowed distance from market price (%)
            
        Returns:
            Order result or None if failed
        """
        try:
            # Calculate distance from market price
            distance_info = self.calculate_limit_order_distance(symbol, price)
            if not distance_info:
                self.logger.error("Could not calculate distance from market price")
                return None
            
            # Check if distance is within allowed range
            if distance_info['percentage_distance'] > max_distance_pct:
                self.logger.error(
                    f"Limit order price {price} is {distance_info['percentage_distance']:.2f}% "
                    f"from market price {distance_info['market_price']}, "
                    f"exceeding maximum allowed distance of {max_distance_pct}%"
                )
                return None
            
            # Validate order direction makes sense
            market_price = distance_info['market_price']
            if side.upper() == 'BUY' and price > market_price:
                self.logger.warning(f"BUY limit order at {price} is above market price {market_price}")
            elif side.upper() == 'SELL' and price < market_price:
                self.logger.warning(f"SELL limit order at {price} is below market price {market_price}")
            
            self.logger.info(
                f"Limit order distance check passed: {distance_info['percentage_distance']:.2f}% "
                f"{distance_info['direction']} market"
            )
            
            # Place the order
            return self.place_limit_order(symbol, side, quantity, price)
            
        except Exception as e:
            self.logger.error(f"Error in limit order with distance check: {str(e)}")
            return None
    
    def place_iceberg_order(self, symbol: str, side: str, total_quantity: float, 
                           price: float, iceberg_qty: float) -> Optional[List[Dict[str, Any]]]:
        """
        Place an iceberg order (split large order into smaller visible chunks)
        
        Args:
            symbol: Trading symbol
            side: Order side
            total_quantity: Total quantity to trade
            price: Order price
            iceberg_qty: Size of each visible chunk
            
        Returns:
            List of order results or None if failed
        """
        try:
            self.logger.info(f"Placing iceberg order: {symbol} {side} total={total_quantity} @ {price}, chunk={iceberg_qty}")
            
            orders = []
            remaining_qty = total_quantity
            
            while remaining_qty > 0:
                current_qty = min(remaining_qty, iceberg_qty)
                
                order = self.place_limit_order(symbol, side, current_qty, price)
                if order:
                    orders.append(order)
                    remaining_qty -= current_qty
                    self.logger.info(f"Iceberg chunk placed: {current_qty}, remaining: {remaining_qty}")
                    
                    # Wait a moment between orders to avoid rate limits
                    time.sleep(0.1)
                else:
                    self.logger.error(f"Failed to place iceberg chunk, stopping. Placed {len(orders)} orders")
                    break
            
            if orders:
                self.logger.info(f"Iceberg order completed: {len(orders)} orders placed")
                return orders
            else:
                self.logger.error("Failed to place any iceberg orders")
                return None
                
        except Exception as e:
            self.logger.error(f"Error placing iceberg order: {str(e)}")
            return None
    
    def place_bracket_order(self, symbol: str, side: str, quantity: float, 
                           entry_price: float, take_profit_price: float, 
                           stop_loss_price: float) -> Optional[Dict[str, Any]]:
        """
        Place a bracket order (entry + take profit + stop loss)
        
        Args:
            symbol: Trading symbol
            side: Order side for entry
            quantity: Order quantity
            entry_price: Entry price
            take_profit_price: Take profit price
            stop_loss_price: Stop loss price
            
        Returns:
            Dict with all order results or None if failed
        """
        try:
            self.logger.info(
                f"Placing bracket order: {symbol} {side} {quantity} "
                f"entry@{entry_price} TP@{take_profit_price} SL@{stop_loss_price}"
            )
            
            # Place entry order
            entry_order = self.place_limit_order(symbol, side, quantity, entry_price)
            if not entry_order:
                self.logger.error("Failed to place entry order for bracket")
                return None
            
            # Determine exit side (opposite of entry)
            exit_side = 'SELL' if side.upper() == 'BUY' else 'BUY'
            
            # Place take profit order
            tp_order = self.place_limit_order(symbol, exit_side, quantity, take_profit_price)
            if not tp_order:
                self.logger.warning("Failed to place take profit order, but entry order is placed")
            
            # Place stop loss order (would need stop-limit implementation)
            # For now, we'll just log it as we need stop-limit functionality
            self.logger.info(f"Stop loss at {stop_loss_price} should be implemented with stop-limit order")
            
            result = {
                'entry_order': entry_order,
                'take_profit_order': tp_order,
                'stop_loss_price': stop_loss_price,
                'status': 'partial' if not tp_order else 'complete'
            }
            
            self.logger.info(f"Bracket order placed: entry={entry_order.get('orderId')}, TP={tp_order.get('orderId') if tp_order else 'failed'}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error placing bracket order: {str(e)}")
            return None
