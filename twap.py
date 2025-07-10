"""
TWAP (Time-Weighted Average Price) Order Manager for Binance Futures
Handles splitting large orders into smaller chunks over time
"""

from typing import Optional, Dict, Any, List
import sys
import os
import time
import threading
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from logger import setup_logger, log_order_action

class TWAPOrderManager:
    """
    Manages TWAP order placement and execution
    """
    
    def __init__(self, binance_client):
        """Initialize TWAP order manager"""
        self.client = binance_client
        self.logger = setup_logger('TWAPOrderManager')
        self.active_twap_orders = {}
        self.monitoring_threads = {}
        self.logger.info("TWAP Order Manager initialized")
    
    def place_twap_order(self, symbol: str, side: str, total_quantity: float, 
                        duration_minutes: int, interval_seconds: int) -> Optional[Dict[str, Any]]:
        """
        Place a TWAP order (split large order into smaller chunks)
        
        Args:
            symbol: Trading symbol
            side: Order side (BUY/SELL)
            total_quantity: Total quantity to trade
            duration_minutes: Duration over which to execute the order
            interval_seconds: Time interval between each chunk
            
        Returns:
            Dict containing TWAP order result or None if failed
        """
        try:
            self.logger.info(f"Placing TWAP order: {symbol} {side} {total_quantity} duration={duration_minutes}m interval={interval_seconds}s")
            
            # Calculate number of chunks
            total_intervals = max(1, duration_minutes * 60 // interval_seconds)  # Avoid division by zero
            chunk_quantity = total_quantity / total_intervals
            
            # Log the order action
            log_order_action(
                self.logger,
                'PLACE_TWAP',
                symbol,
                side,
                total_quantity,
                price=None
            )
            
            # Create TWAP order record
            twap_id = f"TWAP_{int(time.time() * 1000)}"
            twap_order = {
                'twap_id': twap_id,
                'symbol': symbol,
                'side': side,
                'total_quantity': total_quantity,
                'duration_minutes': duration_minutes,
                'interval_seconds': interval_seconds,
                'chunk_quantity': chunk_quantity,
                'remaining_quantity': total_quantity,
                'status': 'active',
                'created_time': time.time()
            }
            
            # Store TWAP order
            self.active_twap_orders[twap_id] = twap_order
            
            # Start execution thread
            self._start_twap_execution(twap_id)
            
            self.logger.info(f"TWAP order placed successfully: {twap_id}")
            
            # Log successful TWAP placement
            log_order_action(
                self.logger,
                'PLACED_TWAP',
                symbol,
                side,
                total_quantity,
                order_id=twap_id
            )
            
            return {
                'job_id': twap_id,
                'symbol': symbol,
                'side': side,
                'total_quantity': total_quantity,
                'status': 'active'
            }
            
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Error placing TWAP order: {error_msg}")
            
            # Log error
            log_order_action(
                self.logger,
                'ERROR_TWAP',
                symbol,
                side,
                total_quantity,
                error=error_msg
            )
            
            return None
    
    def _execute_twap_chunk(self, twap_order: Dict[str, Any]):
        """Execute a chunk of the TWAP order"""
        try:
            symbol = twap_order['symbol']
            side = twap_order['side']
            chunk_quantity = twap_order['chunk_quantity']
            
            # Place market order
            order_result = self.client.place_order(
                symbol=symbol,
                side=side,
                order_type='MARKET',
                quantity=chunk_quantity
            )
            
            if order_result:
                self.logger.info(f"TWAP chunk executed: {symbol} {side} {chunk_quantity}")
                return True
            else:
                self.logger.error(f"Failed to execute TWAP chunk: {symbol} {side} {chunk_quantity}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error executing TWAP chunk: {str(e)}")
            return False
    
    def _start_twap_execution(self, twap_id: str):
        """Start execution thread for TWAP order"""
        def execute_twap():
            try:
                self.logger.info(f"Starting TWAP execution for {twap_id}")
                
                twap_order = self.active_twap_orders[twap_id]
                total_intervals = max(1, twap_order['duration_minutes'] * 60 // twap_order['interval_seconds'])
                
                for _ in range(total_intervals):
                    if twap_order['status'] != 'active':
                        break
                    
                    if not self._execute_twap_chunk(twap_order):
                        twap_order['status'] = 'failed'
                        break
                    
                    twap_order['remaining_quantity'] -= twap_order['chunk_quantity']
                    
                    # Wait before placing next chunk
                    time.sleep(twap_order['interval_seconds'])
                    
                twap_order['status'] = 'completed'
                twap_order['completed_time'] = time.time()
                self.logger.info(f"TWAP execution completed for {twap_id}")
                
                # Remove from active orders
                if twap_id in self.active_twap_orders:
                    del self.active_twap_orders[twap_id]
                
            except Exception as e:
                self.logger.error(f"Error in TWAP execution: {str(e)}")
        
        # Start the execution thread
        thread = threading.Thread(target=execute_twap, daemon=True)
        thread.start()
        self.monitoring_threads[twap_id] = thread
    
    def cancel_twap_order(self, twap_id: str) -> bool:
        """Cancel a TWAP order""
        try:
            if twap_id not in self.active_twap_orders:
                self.logger.error(f"TWAP order {twap_id} not found")
                return False
            
            twap_order = self.active_twap_orders[twap_id]
            twap_order['status'] = 'cancelled'
            twap_order['completed_time'] = time.time()
            self.logger.info(f"TWAP order {twap_id} cancelled")
            return True
            
        except Exception as e:
            self.logger.error(f"Error cancelling TWAP order {twap_id}: {str(e)}")
            return False
    
    def get_twap_order_status(self, twap_id: str) -> Optional[Dict[str, Any]]:
        """Get TWAP order status""
        try:
            return self.active_twap_orders.get(twap_id, None)
        except Exception as e:
            self.logger.error(f"Error getting TWAP order status: {str(e)}")
            return None
    
    def list_active_twap_orders(self) -> List[Dict[str, Any]]:
        """List all active TWAP orders""
        try:
            return list(self.active_twap_orders.values())
        except Exception as e:
            self.logger.error(f"Error listing active TWAP orders: {str(e)}")
            return []
    
    def cleanup_completed_twap_orders(self, max_age_hours: int = 24):
        """Clean up completed TWAP orders older than specified hours""
        try:
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            completed_orders = []
            
            for twap_id, twap_order in list(self.active_twap_orders.items()):
                if twap_order['status'] != 'active':
                    completed_time = twap_order.get('completed_time', twap_order['created_time'])
                    age_seconds = current_time - completed_time
                    
                    if age_seconds > max_age_seconds:
                        completed_orders.append(twap_id)
            
            for twap_id in completed_orders:
                del self.active_twap_orders[twap_id]
                self.logger.info(f"Cleaned up completed TWAP order: {twap_id}")
            
            if completed_orders:
                self.logger.info(f"Cleaned up {len(completed_orders)} completed TWAP orders")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up completed TWAP orders: {str(e)}")

