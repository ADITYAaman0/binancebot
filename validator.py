"""
Input validation module for Binance Futures Bot
Validates all input parameters before placing orders
"""

import re
from typing import Optional, List, Dict, Any
from decimal import Decimal, InvalidOperation
from logger import setup_logger

class OrderValidator:
    """
    Validates order parameters before execution
    """
    
    def __init__(self, binance_client):
        """Initialize validator with Binance client"""
        self.client = binance_client
        self.logger = setup_logger('OrderValidator')
        self.exchange_info = None
        self.symbols_info = {}
        self._load_exchange_info()
    
    def _load_exchange_info(self):
        """Load exchange information for validation"""
        try:
            self.exchange_info = self.client.get_exchange_info()
            if self.exchange_info:
                for symbol_info in self.exchange_info.get('symbols', []):
                    self.symbols_info[symbol_info['symbol']] = symbol_info
                self.logger.info(f"Loaded exchange info for {len(self.symbols_info)} symbols")
            else:
                self.logger.warning("Failed to load exchange info")
        except Exception as e:
            self.logger.error(f"Error loading exchange info: {str(e)}")
    
    def validate_symbol(self, symbol: str) -> bool:
        """
        Validate trading symbol
        
        Args:
            symbol: Trading symbol (e.g., BTCUSDT)
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not symbol or not isinstance(symbol, str):
            self.logger.error("Symbol must be a non-empty string")
            return False
        
        symbol = symbol.upper()
        
        # Basic format validation
        if not re.match(r'^[A-Z0-9]{6,20}$', symbol):
            self.logger.error(f"Invalid symbol format: {symbol}")
            return False
        
        # Check against exchange info if available
        if self.symbols_info:
            if symbol not in self.symbols_info:
                self.logger.error(f"Symbol not found in exchange: {symbol}")
                return False
            
            symbol_info = self.symbols_info[symbol]
            if symbol_info.get('status') != 'TRADING':
                self.logger.error(f"Symbol not available for trading: {symbol}")
                return False
        
        return True
    
    def validate_side(self, side: str) -> bool:
        """
        Validate order side
        
        Args:
            side: Order side (BUY/SELL)
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not side or not isinstance(side, str):
            self.logger.error("Side must be a non-empty string")
            return False
        
        side = side.upper()
        if side not in ['BUY', 'SELL']:
            self.logger.error(f"Invalid side: {side}. Must be BUY or SELL")
            return False
        
        return True
    
    def validate_quantity(self, quantity: Any) -> bool:
        """
        Validate order quantity
        
        Args:
            quantity: Order quantity
            
        Returns:
            bool: True if valid, False otherwise
        """
        if quantity is None:
            self.logger.error("Quantity cannot be None")
            return False
        
        # Convert to string for validation
        quantity_str = str(quantity)
        
        # Check if it's a valid number
        try:
            quantity_decimal = Decimal(quantity_str)
        except (InvalidOperation, ValueError):
            self.logger.error(f"Invalid quantity format: {quantity}")
            return False
        
        # Check if quantity is positive
        if quantity_decimal <= 0:
            self.logger.error(f"Quantity must be positive: {quantity}")
            return False
        
        # Check for reasonable limits
        if quantity_decimal > Decimal('1000000'):
            self.logger.error(f"Quantity too large: {quantity}")
            return False
        
        return True
    
    def validate_price(self, price: Any) -> bool:
        """
        Validate order price
        
        Args:
            price: Order price
            
        Returns:
            bool: True if valid, False otherwise
        """
        if price is None:
            self.logger.error("Price cannot be None")
            return False
        
        # Convert to string for validation
        price_str = str(price)
        
        # Check if it's a valid number
        try:
            price_decimal = Decimal(price_str)
        except (InvalidOperation, ValueError):
            self.logger.error(f"Invalid price format: {price}")
            return False
        
        # Check if price is positive
        if price_decimal <= 0:
            self.logger.error(f"Price must be positive: {price}")
            return False
        
        # Check for reasonable limits
        if price_decimal > Decimal('10000000'):
            self.logger.error(f"Price too large: {price}")
            return False
        
        return True
    
    def validate_order_type(self, order_type: str) -> bool:
        """
        Validate order type
        
        Args:
            order_type: Order type (LIMIT, MARKET, STOP, etc.)
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not order_type or not isinstance(order_type, str):
            self.logger.error("Order type must be a non-empty string")
            return False
        
        valid_types = [
            'LIMIT', 'MARKET', 'STOP', 'STOP_MARKET', 
            'TAKE_PROFIT', 'TAKE_PROFIT_MARKET', 'TRAILING_STOP_MARKET'
        ]
        
        order_type = order_type.upper()
        if order_type not in valid_types:
            self.logger.error(f"Invalid order type: {order_type}")
            return False
        
        return True
    
    def validate_time_in_force(self, time_in_force: str) -> bool:
        """
        Validate time in force
        
        Args:
            time_in_force: Time in force (GTC, IOC, FOK)
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not time_in_force or not isinstance(time_in_force, str):
            self.logger.error("Time in force must be a non-empty string")
            return False
        
        valid_tif = ['GTC', 'IOC', 'FOK', 'GTX']
        
        time_in_force = time_in_force.upper()
        if time_in_force not in valid_tif:
            self.logger.error(f"Invalid time in force: {time_in_force}")
            return False
        
        return True
    
    def validate_symbol_specific(self, symbol: str, quantity: float, price: float = None) -> bool:
        """
        Validate symbol-specific constraints
        
        Args:
            symbol: Trading symbol
            quantity: Order quantity
            price: Order price (optional)
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not self.symbols_info or symbol not in self.symbols_info:
            self.logger.warning(f"No symbol info available for {symbol}, skipping specific validation")
            return True
        
        symbol_info = self.symbols_info[symbol]
        
        # Get filters
        filters = {f['filterType']: f for f in symbol_info.get('filters', [])}
        
        # Validate LOT_SIZE
        if 'LOT_SIZE' in filters:
            lot_filter = filters['LOT_SIZE']
            min_qty = float(lot_filter['minQty'])
            max_qty = float(lot_filter['maxQty'])
            step_size = float(lot_filter['stepSize'])
            
            if quantity < min_qty:
                self.logger.error(f"Quantity {quantity} below minimum {min_qty}")
                return False
            
            if quantity > max_qty:
                self.logger.error(f"Quantity {quantity} above maximum {max_qty}")
                return False
            
            # Check step size
            if step_size > 0:
                remainder = (quantity - min_qty) % step_size
                if remainder != 0:
                    self.logger.error(f"Quantity {quantity} doesn't match step size {step_size}")
                    return False
        
        # Validate PRICE_FILTER
        if price is not None and 'PRICE_FILTER' in filters:
            price_filter = filters['PRICE_FILTER']
            min_price = float(price_filter['minPrice'])
            max_price = float(price_filter['maxPrice'])
            tick_size = float(price_filter['tickSize'])
            
            if price < min_price:
                self.logger.error(f"Price {price} below minimum {min_price}")
                return False
            
            if price > max_price:
                self.logger.error(f"Price {price} above maximum {max_price}")
                return False
            
            # Check tick size
            if tick_size > 0:
                remainder = (price - min_price) % tick_size
                if remainder != 0:
                    self.logger.error(f"Price {price} doesn't match tick size {tick_size}")
                    return False
        
        # Validate MIN_NOTIONAL
        if price is not None and 'MIN_NOTIONAL' in filters:
            notional_filter = filters['MIN_NOTIONAL']
            min_notional = float(notional_filter['minNotional'])
            
            notional_value = quantity * price
            if notional_value < min_notional:
                self.logger.error(f"Notional value {notional_value} below minimum {min_notional}")
                return False
        
        return True
    
    def validate_market_order(self, symbol: str, side: str, quantity: float) -> bool:
        """
        Validate market order parameters
        
        Args:
            symbol: Trading symbol
            side: Order side
            quantity: Order quantity
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not self.validate_symbol(symbol):
            return False
        
        if not self.validate_side(side):
            return False
        
        if not self.validate_quantity(quantity):
            return False
        
        if not self.validate_symbol_specific(symbol, quantity):
            return False
        
        self.logger.info(f"Market order validation passed: {symbol} {side} {quantity}")
        return True
    
    def validate_limit_order(self, symbol: str, side: str, quantity: float, price: float) -> bool:
        """
        Validate limit order parameters
        
        Args:
            symbol: Trading symbol
            side: Order side
            quantity: Order quantity
            price: Order price
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not self.validate_symbol(symbol):
            return False
        
        if not self.validate_side(side):
            return False
        
        if not self.validate_quantity(quantity):
            return False
        
        if not self.validate_price(price):
            return False
        
        if not self.validate_symbol_specific(symbol, quantity, price):
            return False
        
        self.logger.info(f"Limit order validation passed: {symbol} {side} {quantity} @ {price}")
        return True
    
    def validate_stop_limit_order(self, symbol: str, side: str, quantity: float, 
                                 stop_price: float, limit_price: float) -> bool:
        """
        Validate stop-limit order parameters
        
        Args:
            symbol: Trading symbol
            side: Order side
            quantity: Order quantity
            stop_price: Stop price
            limit_price: Limit price
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not self.validate_symbol(symbol):
            return False
        
        if not self.validate_side(side):
            return False
        
        if not self.validate_quantity(quantity):
            return False
        
        if not self.validate_price(stop_price):
            return False
        
        if not self.validate_price(limit_price):
            return False
        
        # Validate stop price vs limit price logic
        if side.upper() == 'BUY':
            if stop_price <= limit_price:
                self.logger.error("For BUY stop-limit, stop price must be > limit price")
                return False
        else:  # SELL
            if stop_price >= limit_price:
                self.logger.error("For SELL stop-limit, stop price must be < limit price")
                return False
        
        if not self.validate_symbol_specific(symbol, quantity, limit_price):
            return False
        
        self.logger.info(f"Stop-limit order validation passed: {symbol} {side} {quantity} stop@{stop_price} limit@{limit_price}")
        return True
    
    def validate_oco_order(self, symbol: str, side: str, quantity: float, 
                          take_profit_price: float, stop_loss_price: float) -> bool:
        """
        Validate OCO order parameters
        
        Args:
            symbol: Trading symbol
            side: Order side
            quantity: Order quantity
            take_profit_price: Take profit price
            stop_loss_price: Stop loss price
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not self.validate_symbol(symbol):
            return False
        
        if not self.validate_side(side):
            return False
        
        if not self.validate_quantity(quantity):
            return False
        
        if not self.validate_price(take_profit_price):
            return False
        
        if not self.validate_price(stop_loss_price):
            return False
        
        # Validate price relationships
        if side.upper() == 'SELL':
            if take_profit_price <= stop_loss_price:
                self.logger.error("For SELL OCO, take profit must be > stop loss")
                return False
        else:  # BUY
            if take_profit_price >= stop_loss_price:
                self.logger.error("For BUY OCO, take profit must be < stop loss")
                return False
        
        if not self.validate_symbol_specific(symbol, quantity, take_profit_price):
            return False
        
        self.logger.info(f"OCO order validation passed: {symbol} {side} {quantity} TP@{take_profit_price} SL@{stop_loss_price}")
        return True
    
    def validate_percentage(self, percentage: float, min_val: float = 0.0, max_val: float = 100.0) -> bool:
        """
        Validate percentage values
        
        Args:
            percentage: Percentage value
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not isinstance(percentage, (int, float)):
            self.logger.error("Percentage must be a number")
            return False
        
        if percentage < min_val or percentage > max_val:
            self.logger.error(f"Percentage {percentage} must be between {min_val} and {max_val}")
            return False
        
        return True
    
    def validate_duration(self, duration: int, min_seconds: int = 60, max_seconds: int = 86400) -> bool:
        """
        Validate duration in seconds
        
        Args:
            duration: Duration in seconds
            min_seconds: Minimum allowed duration
            max_seconds: Maximum allowed duration
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not isinstance(duration, int):
            self.logger.error("Duration must be an integer")
            return False
        
        if duration < min_seconds or duration > max_seconds:
            self.logger.error(f"Duration {duration} must be between {min_seconds} and {max_seconds} seconds")
            return False
        
        return True
