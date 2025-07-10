"""
Binance API Client for Futures Trading
Handles all API communications with Binance
"""

import hashlib
import hmac
import time
import requests
from urllib.parse import urlencode
from typing import Dict, List, Optional, Any
from logger import setup_logger

class BinanceClient:
    """Binance Futures API Client"""
    
    def __init__(self, F8wmuzN5RQiQXZdLUh1rlzQGR2YDrUJuxHNblQS1fwbeblElqHjQxylg7CQSu6NL: str, Y5sg3jC1K8GYsP7vAgambxRzrNCqfbNa8HppuFxW8Q17TUJAASnF34l5KiJBRxyy: str, testnet: bool = False):
        """Initialize Binance client"""
        self.api_key = F8wmuzN5RQiQXZdLUh1rlzQGR2YDrUJuxHNblQS1fwbeblElqHjQxylg7CQSu6NL
        self.secret_key = Y5sg3jC1K8GYsP7vAgambxRzrNCqfbNa8HppuFxW8Q17TUJAASnF34l5KiJBRxyy
        self.testnet = testnet
        self.logger = setup_logger('BinanceClient')
        
        # API endpoints
        if testnet:
            self.base_url = 'https://testnet.binancefuture.com'
        else:
            self.base_url = 'https://fapi.binance.com'
        
        self.logger.info(f"Initialized Binance client (testnet: {testnet})")
    
    def _get_signature(self, params: Dict[str, Any]) -> str:
        """Generate signature for API request"""
        query_string = urlencode(params)
        return hmac.new(
            self.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, signed: bool = True) -> Optional[Dict]:
        """Make API request to Binance"""
        try:
            url = f"{self.base_url}{endpoint}"
            headers = {
                'X-MBX-APIKEY': self.api_key,
                'Content-Type': 'application/json'
            }
            
            if params is None:
                params = {}
            
            if signed:
                params['timestamp'] = int(time.time() * 1000)
                params['signature'] = self._get_signature(params)
            
            self.logger.debug(f"Making {method} request to {endpoint}")
            
            if method == 'GET':
                response = requests.get(url, params=params, headers=headers)
            elif method == 'POST':
                response = requests.post(url, params=params, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, params=params, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"API request failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error making API request: {str(e)}")
            return None
    
    def get_server_time(self) -> Optional[Dict]:
        """Get server time"""
        return self._make_request('GET', '/fapi/v1/time', signed=False)
    
    def get_exchange_info(self) -> Optional[Dict]:
        """Get exchange information"""
        return self._make_request('GET', '/fapi/v1/exchangeInfo', signed=False)
    
    def get_account_balance(self) -> Optional[List[Dict]]:
        """Get account balance"""
        result = self._make_request('GET', '/fapi/v2/account')
        if result:
            return result.get('assets', [])
        return None
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict]:
        """Get symbol information"""
        exchange_info = self.get_exchange_info()
        if exchange_info:
            for symbol_info in exchange_info.get('symbols', []):
                if symbol_info['symbol'] == symbol:
                    return symbol_info
        return None
    
    def get_ticker_price(self, symbol: str) -> Optional[Dict]:
        """Get current ticker price"""
        params = {'symbol': symbol}
        return self._make_request('GET', '/fapi/v1/ticker/price', params, signed=False)
    
    def place_order(self, symbol: str, side: str, order_type: str, quantity: float, 
                   price: float = None, stop_price: float = None, **kwargs) -> Optional[Dict]:
        """Place a new order"""
        params = {
            'symbol': symbol,
            'side': side,
            'type': order_type,
            'quantity': quantity,
        }
        
        if price is not None:
            params['price'] = price
        
        if stop_price is not None:
            params['stopPrice'] = stop_price
        
        # Add any additional parameters
        params.update(kwargs)
        
        self.logger.info(f"Placing {order_type} order: {symbol} {side} {quantity}")
        result = self._make_request('POST', '/fapi/v1/order', params)
        
        if result:
            self.logger.info(f"Order placed successfully: {result.get('orderId')}")
        else:
            self.logger.error("Failed to place order")
        
        return result
    
    def cancel_order(self, symbol: str, order_id: str) -> Optional[Dict]:
        """Cancel an order"""
        params = {
            'symbol': symbol,
            'orderId': order_id
        }
        
        self.logger.info(f"Cancelling order: {order_id}")
        result = self._make_request('DELETE', '/fapi/v1/order', params)
        
        if result:
            self.logger.info(f"Order cancelled successfully: {order_id}")
        else:
            self.logger.error(f"Failed to cancel order: {order_id}")
        
        return result
    
    def get_open_orders(self, symbol: str = None) -> Optional[List[Dict]]:
        """Get open orders"""
        params = {}
        if symbol:
            params['symbol'] = symbol
        
        return self._make_request('GET', '/fapi/v1/openOrders', params)
    
    def get_order_history(self, symbol: str, limit: int = 500) -> Optional[List[Dict]]:
        """Get order history"""
        params = {
            'symbol': symbol,
            'limit': limit
        }
        
        return self._make_request('GET', '/fapi/v1/allOrders', params)
    
    def get_order_status(self, symbol: str, order_id: str) -> Optional[Dict]:
        """Get order status"""
        params = {
            'symbol': symbol,
            'orderId': order_id
        }
        
        return self._make_request('GET', '/fapi/v1/order', params)
    
    def place_oco_order(self, symbol: str, side: str, quantity: float, 
                       price: float, stop_price: float, stop_limit_price: float) -> Optional[Dict]:
        """Place OCO order (for spot trading, futures uses different approach)"""
        # Note: Futures doesn't have native OCO, so we'll implement it differently
        # This is a placeholder for the OCO logic
        self.logger.warning("OCO orders not natively supported in futures, implementing custom logic")
        
        # We'll handle this in the OCO order manager
        return None
    
    def get_klines(self, symbol: str, interval: str, limit: int = 500) -> Optional[List[List]]:
        """Get kline/candlestick data"""
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        
        return self._make_request('GET', '/fapi/v1/klines', params, signed=False)
    
    def get_24hr_ticker(self, symbol: str) -> Optional[Dict]:
        """Get 24hr ticker statistics"""
        params = {'symbol': symbol}
        return self._make_request('GET', '/fapi/v1/ticker/24hr', params, signed=False)
    
    def get_position_info(self, symbol: str = None) -> Optional[List[Dict]]:
        """Get position information"""
        params = {}
        if symbol:
            params['symbol'] = symbol
        
        return self._make_request('GET', '/fapi/v2/positionRisk', params)
    
    def change_leverage(self, symbol: str, leverage: int) -> Optional[Dict]:
        """Change leverage for a symbol"""
        params = {
            'symbol': symbol,
            'leverage': leverage
        }
        
        self.logger.info(f"Changing leverage for {symbol} to {leverage}x")
        return self._make_request('POST', '/fapi/v1/leverage', params)
    
    def change_margin_type(self, symbol: str, margin_type: str) -> Optional[Dict]:
        """Change margin type (ISOLATED or CROSSED)"""
        params = {
            'symbol': symbol,
            'marginType': margin_type
        }
        
        self.logger.info(f"Changing margin type for {symbol} to {margin_type}")
        return self._make_request('POST', '/fapi/v1/marginType', params)
    
    def test_connectivity(self) -> bool:
        """Test API connectivity"""
        try:
            result = self.get_server_time()
            if result:
                self.logger.info("API connectivity test passed")
                return True
            else:
                self.logger.error("API connectivity test failed")
                return False
        except Exception as e:
            self.logger.error(f"API connectivity test failed: {str(e)}")
            return False
