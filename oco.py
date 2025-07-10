"""
OCO (One-Cancels-Other) Order Manager for Binance Futures
Since Binance Futures doesn't have native OCO, we implement custom logic
"""

from typing import Optional, Dict, Any, List
import sys
import os
import threading
import time
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from logger import setup_logger, log_order_action

class OCOOrderManager:
    """
    Manages OCO (One-Cancels-Other) order placement and execution
    Custom implementation for Binance Futures
    """
    
    def __init__(self, binance_client):
        """Initialize OCO order manager"""
        self.client = binance_client
        self.logger = setup_logger('OCOOrderManager')
        self.active_oco_orders = {}  # Track active OCO orders
        self.monitoring_threads = {}  # Track monitoring threads
        self.logger.info("OCO Order Manager initialized")
    
    def place_oco_order(self, symbol: str, side: str, quantity: float, 
                       take_profit_price: float, stop_loss_price: float) -> Optional[Dict[str, Any]]:
        """
        Place an OCO order (custom implementation)
        
        Args:
            symbol: Trading symbol
            side: Order side (BUY/SELL for the exit orders)
            quantity: Order quantity
            take_profit_price: Take profit price
            stop_loss_price: Stop loss price
            
        Returns:
            Dict containing OCO order result or None if failed
        """
        try:
            self.logger.info(f"Placing OCO order: {symbol} {side} {quantity} TP@{take_profit_price} SL@{stop_loss_price}")
            
            # Generate OCO order ID
            oco_id = f"OCO_{int(time.time() * 1000)}"
            
            # Log the order action
            log_order_action(
                self.logger,
                'PLACE_OCO',
                symbol,
                side,
                quantity,
                price=take_profit_price
            )
            
            # Place take profit limit order
            tp_order = self._place_take_profit_limit_order(symbol, side, quantity, take_profit_price)
            if not tp_order:
                self.logger.error("Failed to place take profit order for OCO")
                return None
            
            # Place stop loss order
            sl_order = self._place_stop_loss_order(symbol, side, quantity, stop_loss_price)
            if not sl_order:
                self.logger.error("Failed to place stop loss order for OCO")
                # Cancel the take profit order since OCO failed
                self.client.cancel_order(symbol, tp_order['orderId'])
                return None
            
            # Create OCO order record
            oco_order = {
                'oco_id': oco_id,
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'take_profit_order': tp_order,
                'stop_loss_order': sl_order,
                'take_profit_price': take_profit_price,
                'stop_loss_price': stop_loss_price,
                'status': 'active',
                'created_time': time.time()
            }
            
            # Store OCO order
            self.active_oco_orders[oco_id] = oco_order
            
            # Start monitoring thread
            self._start_oco_monitoring(oco_id)
            
            self.logger.info(f"OCO order placed successfully: {oco_id}")
            
            # Log successful OCO placement
            log_order_action(
                self.logger,
                'PLACED_OCO',
                symbol,
                side,
                quantity,
                price=take_profit_price,
                order_id=oco_id
            )
            
            return {
                'orderListId': oco_id,
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'take_profit_order_id': tp_order['orderId'],
                'stop_loss_order_id': sl_order['orderId'],
                'status': 'active'
            }
            
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Error placing OCO order: {error_msg}")
            
            # Log error
            log_order_action(
                self.logger,
                'ERROR_OCO',
                symbol,
                side,
                quantity,
                price=take_profit_price,
                error=error_msg
            )
            
            return None
    
    def _place_take_profit_limit_order(self, symbol: str, side: str, quantity: float, 
                                      price: float) -> Optional[Dict[str, Any]]:
        """Place take profit limit order"""
        try:
            return self.client.place_order(
                symbol=symbol,
                side=side,
                order_type='LIMIT',
                quantity=quantity,
                price=price,
                timeInForce='GTC'
            )
        except Exception as e:
            self.logger.error(f"Error placing take profit limit order: {str(e)}")
            return None
    
    def _place_stop_loss_order(self, symbol: str, side: str, quantity: float, 
                              stop_price: float) -> Optional[Dict[str, Any]]:
        """Place stop loss market order"""
        try:
            return self.client.place_order(
                symbol=symbol,
                side=side,
                order_type='STOP_MARKET',
                quantity=quantity,
                stop_price=stop_price
            )
        except Exception as e:
            self.logger.error(f"Error placing stop loss order: {str(e)}")
            return None
    
    def _start_oco_monitoring(self, oco_id: str):
        """Start monitoring thread for OCO order"""
        def monitor_oco():
            try:
                self.logger.info(f"Starting OCO monitoring for {oco_id}")
                
                while oco_id in self.active_oco_orders:
                    oco_order = self.active_oco_orders[oco_id]
                    
                    if oco_order['status'] != 'active':
                        break
                    
                    # Check order statuses
                    tp_status = self._check_order_status(oco_order['symbol'], oco_order['take_profit_order']['orderId'])
                    sl_status = self._check_order_status(oco_order['symbol'], oco_order['stop_loss_order']['orderId'])
                    
                    # If take profit is filled, cancel stop loss
                    if tp_status and tp_status.get('status') == 'FILLED':
                        self.logger.info(f"Take profit filled for OCO {oco_id}, cancelling stop loss")
                        self._cancel_remaining_order(oco_order, 'stop_loss')
                        oco_order['status'] = 'completed_tp'
                        oco_order['completed_time'] = time.time()
                        break
                    
                    # If stop loss is filled, cancel take profit
                    elif sl_status and sl_status.get('status') == 'FILLED':
                        self.logger.info(f"Stop loss filled for OCO {oco_id}, cancelling take profit")
                        self._cancel_remaining_order(oco_order, 'take_profit')
                        oco_order['status'] = 'completed_sl'
                        oco_order['completed_time'] = time.time()
                        break
                    
                    # If either order is cancelled externally, cancel the other
                    elif (tp_status and tp_status.get('status') == 'CANCELED') or \
                         (sl_status and sl_status.get('status') == 'CANCELED'):
                        self.logger.info(f"One order cancelled externally for OCO {oco_id}, cancelling the other")
                        if tp_status and tp_status.get('status') == 'CANCELED':
                            self._cancel_remaining_order(oco_order, 'stop_loss')
                        else:
                            self._cancel_remaining_order(oco_order, 'take_profit')
                        oco_order['status'] = 'cancelled'
                        oco_order['completed_time'] = time.time()
                        break
                    
                    # Wait before next check
                    time.sleep(2)  # Check every 2 seconds
                
                # Clean up
                if oco_id in self.active_oco_orders:
                    self.logger.info(f"OCO monitoring completed for {oco_id}: {self.active_oco_orders[oco_id]['status']}")
                
                # Remove from monitoring threads
                if oco_id in self.monitoring_threads:
                    del self.monitoring_threads[oco_id]
                    
            except Exception as e:
                self.logger.error(f"Error in OCO monitoring for {oco_id}: {str(e)}")
        
        # Start the monitoring thread
        thread = threading.Thread(target=monitor_oco, daemon=True)
        thread.start()
        self.monitoring_threads[oco_id] = thread
    
    def _check_order_status(self, symbol: str, order_id: str) -> Optional[Dict[str, Any]]:
        """Check the status of an order"""
        try:
            return self.client.get_order_status(symbol, order_id)
        except Exception as e:
            self.logger.debug(f"Error checking order status {order_id}: {str(e)}")
            return None
    
    def _cancel_remaining_order(self, oco_order: Dict[str, Any], order_type: str):
        """Cancel the remaining order in OCO"""
        try:
            symbol = oco_order['symbol']
            
            if order_type == 'take_profit':
                order_id = oco_order['take_profit_order']['orderId']
                self.logger.info(f"Cancelling take profit order {order_id}")
            else:  # stop_loss
                order_id = oco_order['stop_loss_order']['orderId']
                self.logger.info(f"Cancelling stop loss order {order_id}")
            
            result = self.client.cancel_order(symbol, order_id)
            if result:
                self.logger.info(f"Successfully cancelled {order_type} order {order_id}")
            else:
                self.logger.warning(f"Failed to cancel {order_type} order {order_id}")
                
        except Exception as e:
            self.logger.error(f"Error cancelling {order_type} order: {str(e)}")
    
    def cancel_oco_order(self, oco_id: str) -> bool:
        """Cancel an OCO order"""
        try:
            if oco_id not in self.active_oco_orders:
                self.logger.error(f"OCO order {oco_id} not found")
                return False
            
            oco_order = self.active_oco_orders[oco_id]
            
            if oco_order['status'] != 'active':
                self.logger.warning(f"OCO order {oco_id} is not active: {oco_order['status']}")
                return False
            
            symbol = oco_order['symbol']
            
            # Cancel both orders
            tp_cancelled = self.client.cancel_order(symbol, oco_order['take_profit_order']['orderId'])
            sl_cancelled = self.client.cancel_order(symbol, oco_order['stop_loss_order']['orderId'])
            
            if tp_cancelled or sl_cancelled:
                oco_order['status'] = 'cancelled'
                oco_order['completed_time'] = time.time()
                self.logger.info(f"OCO order {oco_id} cancelled")
                return True
            else:
                self.logger.error(f"Failed to cancel OCO order {oco_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error cancelling OCO order {oco_id}: {str(e)}")
            return False
    
    def get_oco_order_status(self, oco_id: str) -> Optional[Dict[str, Any]]:
        """Get OCO order status"""
        try:
            if oco_id not in self.active_oco_orders:
                self.logger.error(f"OCO order {oco_id} not found")
                return None
            
            oco_order = self.active_oco_orders[oco_id]
            
            # Get current order statuses
            tp_status = self._check_order_status(oco_order['symbol'], oco_order['take_profit_order']['orderId'])
            sl_status = self._check_order_status(oco_order['symbol'], oco_order['stop_loss_order']['orderId'])
            
            return {
                'oco_id': oco_id,
                'symbol': oco_order['symbol'],
                'status': oco_order['status'],
                'take_profit_status': tp_status.get('status') if tp_status else 'unknown',
                'stop_loss_status': sl_status.get('status') if sl_status else 'unknown',
                'created_time': oco_order['created_time'],
                'completed_time': oco_order.get('completed_time')
            }
            
        except Exception as e:
            self.logger.error(f"Error getting OCO order status: {str(e)}")
            return None
    
    def list_active_oco_orders(self) -> List[Dict[str, Any]]:
        """List all active OCO orders"""
        try:
            active_orders = []
            
            for oco_id, oco_order in self.active_oco_orders.items():
                if oco_order['status'] == 'active':
                    status_info = self.get_oco_order_status(oco_id)
                    if status_info:
                        active_orders.append(status_info)
            
            return active_orders
            
        except Exception as e:
            self.logger.error(f"Error listing active OCO orders: {str(e)}")
            return []
    
    def place_bracket_oco_order(self, symbol: str, entry_side: str, quantity: float,
                               entry_price: float, take_profit_price: float, 
                               stop_loss_price: float) -> Optional[Dict[str, Any]]:
        """Place a bracket order with entry + OCO exit"""
        try:
            self.logger.info(
                f"Placing bracket OCO order: {symbol} {entry_side} {quantity} "
                f"entry@{entry_price} TP@{take_profit_price} SL@{stop_loss_price}"
            )
            
            # Place entry order first
            entry_order = self.client.place_order(
                symbol=symbol,
                side=entry_side,
                order_type='LIMIT',
                quantity=quantity,
                price=entry_price,
                timeInForce='GTC'
            )
            
            if not entry_order:
                self.logger.error("Failed to place entry order for bracket OCO")
                return None
            
            # Determine exit side
            exit_side = 'SELL' if entry_side.upper() == 'BUY' else 'BUY'
            
            # Place OCO for exit (will be triggered when entry fills)
            # For now, we place the OCO immediately
            # In a full implementation, we'd monitor the entry order and place OCO when it fills
            oco_result = self.place_oco_order(symbol, exit_side, quantity, take_profit_price, stop_loss_price)
            
            if oco_result:
                result = {
                    'entry_order': entry_order,
                    'oco_order': oco_result,
                    'type': 'bracket_oco'
                }
                
                self.logger.info(
                    f"Bracket OCO placed: entry={entry_order['orderId']}, oco={oco_result['orderListId']}"
                )
                return result
            else:
                self.logger.error("Failed to place OCO for bracket order")
                # Cancel entry order since bracket failed
                self.client.cancel_order(symbol, entry_order['orderId'])
                return None
                
        except Exception as e:
            self.logger.error(f"Error placing bracket OCO order: {str(e)}")
            return None
    
    def cleanup_completed_orders(self, max_age_hours: int = 24):
        """Clean up completed OCO orders older than specified hours"""
        try:
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            completed_orders = []
            
            for oco_id, oco_order in list(self.active_oco_orders.items()):
                if oco_order['status'] != 'active':
                    completed_time = oco_order.get('completed_time', oco_order['created_time'])
                    age_seconds = current_time - completed_time
                    
                    if age_seconds > max_age_seconds:
                        completed_orders.append(oco_id)
            
            for oco_id in completed_orders:
                del self.active_oco_orders[oco_id]
                self.logger.info(f"Cleaned up completed OCO order: {oco_id}")
            
            if completed_orders:
                self.logger.info(f"Cleaned up {len(completed_orders)} completed OCO orders")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up completed orders: {str(e)}")
