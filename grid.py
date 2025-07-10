"""
Grid Order Manager for Binance Futures
Handles grid trading strategy implementation
"""

from typing import Optional, Dict, Any, List
import sys
import os
import time
import threading
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from logger import setup_logger, log_order_action

class GridOrderManager:
    """
    Manages grid order placement and execution
    """
    
    def __init__(self, binance_client):
        """Initialize grid order manager"""
        self.client = binance_client
        self.logger = setup_logger('GridOrderManager')
        self.active_grid_orders = {}
        self.monitoring_threads = {}
        self.logger.info("Grid Order Manager initialized")
    
    def place_grid_order(self, symbol: str, grid_count: int, price_range_min: float, 
                        price_range_max: float, total_quantity: float) -> Optional[Dict[str, Any]]:
        """
        Place a grid order strategy
        
        Args:
            symbol: Trading symbol
            grid_count: Number of grid levels
            price_range_min: Minimum price of the grid
            price_range_max: Maximum price of the grid
            total_quantity: Total quantity to distribute across grid
            
        Returns:
            Dict containing grid order result or None if failed
        """
        try:
            self.logger.info(f"Placing grid order: {symbol} {grid_count} levels {price_range_min}-{price_range_max} qty={total_quantity}")
            
            # Validate inputs
            if grid_count < 2:
                self.logger.error("Grid count must be at least 2")
                return None
            
            if price_range_min >= price_range_max:
                self.logger.error("Price range min must be less than max")
                return None
            
            # Calculate grid levels
            price_step = (price_range_max - price_range_min) / (grid_count - 1)
            quantity_per_level = total_quantity / grid_count
            
            grid_id = f"GRID_{int(time.time() * 1000)}"
            
            # Log the order action
            log_order_action(
                self.logger,
                'PLACE_GRID',
                symbol,
                'BUY/SELL',
                total_quantity,
                price=price_range_min
            )
            
            # Place initial grid orders
            grid_orders = []
            
            for i in range(grid_count):
                price = price_range_min + (i * price_step)
                
                # Alternate between buy and sell orders
                # Lower prices = buy orders, higher prices = sell orders
                mid_price = (price_range_min + price_range_max) / 2
                
                if price < mid_price:
                    side = 'BUY'
                else:
                    side = 'SELL'
                
                # Place limit order
                order_result = self.client.place_order(
                    symbol=symbol,
                    side=side,
                    order_type='LIMIT',
                    quantity=quantity_per_level,
                    price=price,
                    timeInForce='GTC'
                )
                
                if order_result:
                    grid_orders.append({
                        'order_id': order_result['orderId'],
                        'side': side,
                        'price': price,
                        'quantity': quantity_per_level,
                        'status': 'active'
                    })
                    self.logger.info(f"Grid level placed: {side} {quantity_per_level} @ {price}")
                else:
                    self.logger.error(f"Failed to place grid level: {side} {quantity_per_level} @ {price}")
            
            if not grid_orders:
                self.logger.error("Failed to place any grid orders")
                return None
            
            # Create grid order record
            grid_order = {
                'grid_id': grid_id,
                'symbol': symbol,
                'grid_count': grid_count,
                'price_range_min': price_range_min,
                'price_range_max': price_range_max,
                'total_quantity': total_quantity,
                'quantity_per_level': quantity_per_level,
                'price_step': price_step,
                'orders': grid_orders,
                'status': 'active',
                'created_time': time.time()
            }
            
            # Store grid order
            self.active_grid_orders[grid_id] = grid_order
            
            # Start monitoring thread
            self._start_grid_monitoring(grid_id)
            
            self.logger.info(f"Grid order placed successfully: {grid_id} with {len(grid_orders)} levels")
            
            # Log successful grid placement
            log_order_action(
                self.logger,
                'PLACED_GRID',
                symbol,
                'BUY/SELL',
                total_quantity,
                order_id=grid_id
            )
            
            return {
                'grid_id': grid_id,
                'symbol': symbol,
                'orders': grid_orders,
                'status': 'active'
            }
            
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Error placing grid order: {error_msg}")
            
            # Log error
            log_order_action(
                self.logger,
                'ERROR_GRID',
                symbol,
                'BUY/SELL',
                total_quantity,
                error=error_msg
            )
            
            return None
    
    def _start_grid_monitoring(self, grid_id: str):
        """Start monitoring thread for grid order"""
        def monitor_grid():
            try:
                self.logger.info(f"Starting grid monitoring for {grid_id}")
                
                while grid_id in self.active_grid_orders:
                    grid_order = self.active_grid_orders[grid_id]
                    
                    if grid_order['status'] != 'active':
                        break
                    
                    # Check each order in the grid
                    filled_orders = []
                    
                    for order in grid_order['orders']:
                        if order['status'] == 'active':
                            order_status = self._check_order_status(grid_order['symbol'], order['order_id'])
                            
                            if order_status and order_status.get('status') == 'FILLED':
                                self.logger.info(f"Grid order filled: {order['side']} {order['quantity']} @ {order['price']}")
                                order['status'] = 'filled'
                                filled_orders.append(order)
                                
                                # Place replacement order (opposite side)
                                self._place_replacement_order(grid_order, order)
                    
                    # Wait before next check
                    time.sleep(5)  # Check every 5 seconds
                
                self.logger.info(f"Grid monitoring completed for {grid_id}")
                
            except Exception as e:
                self.logger.error(f"Error in grid monitoring for {grid_id}: {str(e)}")
        
        # Start the monitoring thread
        thread = threading.Thread(target=monitor_grid, daemon=True)
        thread.start()
        self.monitoring_threads[grid_id] = thread
    
    def _check_order_status(self, symbol: str, order_id: str) -> Optional[Dict[str, Any]]:
        """Check the status of an order"""
        try:
            return self.client.get_order_status(symbol, order_id)
        except Exception as e:
            self.logger.debug(f"Error checking order status {order_id}: {str(e)}")
            return None
    
    def _place_replacement_order(self, grid_order: Dict[str, Any], filled_order: Dict[str, Any]):
        """Place replacement order when a grid level is filled"""
        try:
            symbol = grid_order['symbol']
            price = filled_order['price']
            quantity = filled_order['quantity']
            
            # Determine replacement order side and price
            if filled_order['side'] == 'BUY':
                # If buy order filled, place sell order at higher price
                new_side = 'SELL'
                new_price = price + grid_order['price_step']
            else:
                # If sell order filled, place buy order at lower price
                new_side = 'BUY'
                new_price = price - grid_order['price_step']
            
            # Check if new price is within grid range
            if (new_price < grid_order['price_range_min'] or 
                new_price > grid_order['price_range_max']):
                self.logger.info(f"Replacement order price {new_price} outside grid range, skipping")
                return
            
            # Place replacement order
            order_result = self.client.place_order(
                symbol=symbol,
                side=new_side,
                order_type='LIMIT',
                quantity=quantity,
                price=new_price,
                timeInForce='GTC'
            )
            
            if order_result:
                # Add new order to grid
                new_order = {
                    'order_id': order_result['orderId'],
                    'side': new_side,
                    'price': new_price,
                    'quantity': quantity,
                    'status': 'active'
                }
                grid_order['orders'].append(new_order)
                
                self.logger.info(f"Replacement order placed: {new_side} {quantity} @ {new_price}")
            else:
                self.logger.error(f"Failed to place replacement order: {new_side} {quantity} @ {new_price}")
                
        except Exception as e:
            self.logger.error(f"Error placing replacement order: {str(e)}")
    
    def cancel_grid_order(self, grid_id: str) -> bool:
        """Cancel a grid order"""
        try:
            if grid_id not in self.active_grid_orders:
                self.logger.error(f"Grid order {grid_id} not found")
                return False
            
            grid_order = self.active_grid_orders[grid_id]
            symbol = grid_order['symbol']
            
            # Cancel all active orders in the grid
            cancelled_count = 0
            for order in grid_order['orders']:
                if order['status'] == 'active':
                    result = self.client.cancel_order(symbol, order['order_id'])
                    if result:
                        order['status'] = 'cancelled'
                        cancelled_count += 1
            
            grid_order['status'] = 'cancelled'
            grid_order['completed_time'] = time.time()
            
            self.logger.info(f"Grid order {grid_id} cancelled, {cancelled_count} orders cancelled")
            return True
            
        except Exception as e:
            self.logger.error(f"Error cancelling grid order {grid_id}: {str(e)}")
            return False
    
    def get_grid_order_status(self, grid_id: str) -> Optional[Dict[str, Any]]:
        """Get grid order status"""
        try:
            if grid_id not in self.active_grid_orders:
                self.logger.error(f"Grid order {grid_id} not found")
                return None
            
            grid_order = self.active_grid_orders[grid_id]
            
            # Count order statuses
            active_orders = sum(1 for order in grid_order['orders'] if order['status'] == 'active')
            filled_orders = sum(1 for order in grid_order['orders'] if order['status'] == 'filled')
            cancelled_orders = sum(1 for order in grid_order['orders'] if order['status'] == 'cancelled')
            
            return {
                'grid_id': grid_id,
                'symbol': grid_order['symbol'],
                'status': grid_order['status'],
                'total_orders': len(grid_order['orders']),
                'active_orders': active_orders,
                'filled_orders': filled_orders,
                'cancelled_orders': cancelled_orders,
                'created_time': grid_order['created_time'],
                'completed_time': grid_order.get('completed_time')
            }
            
        except Exception as e:
            self.logger.error(f"Error getting grid order status: {str(e)}")
            return None
    
    def list_active_grid_orders(self) -> List[Dict[str, Any]]:
        """List all active grid orders"""
        try:
            active_orders = []
            
            for grid_id, grid_order in self.active_grid_orders.items():
                if grid_order['status'] == 'active':
                    status_info = self.get_grid_order_status(grid_id)
                    if status_info:
                        active_orders.append(status_info)
            
            return active_orders
            
        except Exception as e:
            self.logger.error(f"Error listing active grid orders: {str(e)}")
            return []
    
    def get_grid_performance(self, grid_id: str) -> Optional[Dict[str, Any]]:
        """Get grid order performance metrics"""
        try:
            if grid_id not in self.active_grid_orders:
                return None
            
            grid_order = self.active_grid_orders[grid_id]
            
            # Calculate performance metrics
            total_filled = sum(1 for order in grid_order['orders'] if order['status'] == 'filled')
            total_volume = sum(order['quantity'] for order in grid_order['orders'] if order['status'] == 'filled')
            
            # Calculate profit (simplified - would need more detailed tracking in production)
            buy_volume = sum(order['quantity'] for order in grid_order['orders'] 
                           if order['status'] == 'filled' and order['side'] == 'BUY')
            sell_volume = sum(order['quantity'] for order in grid_order['orders'] 
                            if order['status'] == 'filled' and order['side'] == 'SELL')
            
            avg_buy_price = sum(order['price'] * order['quantity'] for order in grid_order['orders'] 
                              if order['status'] == 'filled' and order['side'] == 'BUY') / max(buy_volume, 1)
            avg_sell_price = sum(order['price'] * order['quantity'] for order in grid_order['orders'] 
                               if order['status'] == 'filled' and order['side'] == 'SELL') / max(sell_volume, 1)
            
            return {
                'grid_id': grid_id,
                'total_filled_orders': total_filled,
                'total_volume': total_volume,
                'buy_volume': buy_volume,
                'sell_volume': sell_volume,
                'avg_buy_price': avg_buy_price,
                'avg_sell_price': avg_sell_price,
                'spread': avg_sell_price - avg_buy_price if avg_sell_price > 0 and avg_buy_price > 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error getting grid performance: {str(e)}")
            return None
    
    def cleanup_completed_grid_orders(self, max_age_hours: int = 24):
        """Clean up completed grid orders older than specified hours"""
        try:
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            completed_orders = []
            
            for grid_id, grid_order in list(self.active_grid_orders.items()):
                if grid_order['status'] != 'active':
                    completed_time = grid_order.get('completed_time', grid_order['created_time'])
                    age_seconds = current_time - completed_time
                    
                    if age_seconds > max_age_seconds:
                        completed_orders.append(grid_id)
            
            for grid_id in completed_orders:
                del self.active_grid_orders[grid_id]
                self.logger.info(f"Cleaned up completed grid order: {grid_id}")
            
            if completed_orders:
                self.logger.info(f"Cleaned up {len(completed_orders)} completed grid orders")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up completed grid orders: {str(e)}")
