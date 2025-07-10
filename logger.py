"""
Logging configuration for Binance Futures Bot
Provides structured logging with timestamps and error traces
"""

import logging
import os
from datetime import datetime
from typing import Optional

def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Set up a logger with file and console handlers
    
    Args:
        name: Logger name
        level: Logging level
    
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Create file handler
    log_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'bot.log')
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def log_order_action(logger: logging.Logger, action: str, symbol: str, 
                    side: str, quantity: float, price: Optional[float] = None,
                    order_id: Optional[str] = None, error: Optional[str] = None):
    """
    Log order actions with structured format
    
    Args:
        logger: Logger instance
        action: Action type (PLACE, CANCEL, FILL, etc.)
        symbol: Trading symbol
        side: Order side (BUY/SELL)
        quantity: Order quantity
        price: Order price (optional)
        order_id: Order ID (optional)
        error: Error message (optional)
    """
    log_data = {
        'action': action,
        'symbol': symbol,
        'side': side,
        'quantity': quantity,
        'timestamp': datetime.now().isoformat()
    }
    
    if price is not None:
        log_data['price'] = price
    
    if order_id is not None:
        log_data['order_id'] = order_id
    
    if error is not None:
        log_data['error'] = error
        logger.error(f"ORDER_ACTION: {log_data}")
    else:
        logger.info(f"ORDER_ACTION: {log_data}")

def log_api_call(logger: logging.Logger, endpoint: str, method: str, 
                params: dict, response_code: int, error: Optional[str] = None):
    """
    Log API calls with structured format
    
    Args:
        logger: Logger instance
        endpoint: API endpoint
        method: HTTP method
        params: Request parameters
        response_code: HTTP response code
        error: Error message (optional)
    """
    log_data = {
        'endpoint': endpoint,
        'method': method,
        'params': params,
        'response_code': response_code,
        'timestamp': datetime.now().isoformat()
    }
    
    if error is not None:
        log_data['error'] = error
        logger.error(f"API_CALL: {log_data}")
    else:
        logger.info(f"API_CALL: {log_data}")

def log_execution_trace(logger: logging.Logger, function_name: str, 
                       execution_time: float, success: bool, 
                       error: Optional[str] = None):
    """
    Log function execution traces
    
    Args:
        logger: Logger instance
        function_name: Name of the function
        execution_time: Execution time in seconds
        success: Whether execution was successful
        error: Error message (optional)
    """
    log_data = {
        'function': function_name,
        'execution_time': execution_time,
        'success': success,
        'timestamp': datetime.now().isoformat()
    }
    
    if error is not None:
        log_data['error'] = error
        logger.error(f"EXECUTION_TRACE: {log_data}")
    else:
        logger.info(f"EXECUTION_TRACE: {log_data}")

class BotLogManager:
    """
    Centralized log manager for the bot
    """
    
    def __init__(self, main_logger_name: str = 'BinanceFuturesBot'):
        """Initialize the log manager"""
        self.main_logger = setup_logger(main_logger_name)
        self.loggers = {main_logger_name: self.main_logger}
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get or create a logger"""
        if name not in self.loggers:
            self.loggers[name] = setup_logger(name)
        return self.loggers[name]
    
    def log_bot_startup(self, version: str = "1.0.0"):
        """Log bot startup"""
        self.main_logger.info("=" * 50)
        self.main_logger.info(f"BINANCE FUTURES BOT STARTING - Version {version}")
        self.main_logger.info("=" * 50)
    
    def log_bot_shutdown(self):
        """Log bot shutdown"""
        self.main_logger.info("=" * 50)
        self.main_logger.info("BINANCE FUTURES BOT SHUTTING DOWN")
        self.main_logger.info("=" * 50)
    
    def log_configuration(self, config: dict):
        """Log bot configuration"""
        self.main_logger.info("Bot Configuration:")
        for key, value in config.items():
            # Hide sensitive information
            if 'key' in key.lower() or 'secret' in key.lower():
                value = '*' * 8
            self.main_logger.info(f"  {key}: {value}")
    
    def log_error_with_trace(self, error: Exception, context: str = ""):
        """Log error with full trace"""
        import traceback
        self.main_logger.error(f"Error in {context}: {str(error)}")
        self.main_logger.error(f"Traceback: {traceback.format_exc()}")
    
    def log_performance_metrics(self, metrics: dict):
        """Log performance metrics"""
        self.main_logger.info("Performance Metrics:")
        for metric, value in metrics.items():
            self.main_logger.info(f"  {metric}: {value}")
    
    def create_session_log(self, session_id: str):
        """Create a session-specific log entry"""
        self.main_logger.info(f"Starting trading session: {session_id}")
        self.main_logger.info(f"Session start time: {datetime.now().isoformat()}")
    
    def close_session_log(self, session_id: str, summary: dict):
        """Close a trading session with summary"""
        self.main_logger.info(f"Closing trading session: {session_id}")
        self.main_logger.info(f"Session end time: {datetime.now().isoformat()}")
        self.main_logger.info("Session Summary:")
        for key, value in summary.items():
            self.main_logger.info(f"  {key}: {value}")

# Global log manager instance
_log_manager = None

def get_log_manager() -> BotLogManager:
    """Get the global log manager instance"""
    global _log_manager
    if _log_manager is None:
        _log_manager = BotLogManager()
    return _log_manager
