"""
NOVA Logger
===========
Centralized logging system with security audit trails
"""

import sys
from pathlib import Path
from loguru import logger
from datetime import datetime
import json


class NovaLogger:
    """Enhanced logger for NOVA with security audit capabilities"""
    
    def __init__(self, config):
        self.config = config
        self.logs_dir = config.LOGS_DIR
        self.audit_log = self.logs_dir / "audit.jsonl"
        
        # Remove default logger
        logger.remove()
        
        # Console logger (colored, human-readable)
        logger.add(
            sys.stderr,
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
            level="DEBUG" if config.VERBOSE_LOGGING else "INFO",
            colorize=True
        )
        
        # File logger (detailed)
        logger.add(
            self.logs_dir / "nova_{time:YYYY-MM-DD}.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level="DEBUG",
            rotation="00:00",  # New file at midnight
            retention=f"{config.LOG_RETENTION_DAYS} days",
            compression="zip"
        )
        
        # Error logger (separate file for errors only)
        logger.add(
            self.logs_dir / "errors_{time:YYYY-MM-DD}.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level="ERROR",
            rotation="10 MB",
            retention=f"{config.LOG_RETENTION_DAYS} days"
        )
        
        self.logger = logger
    
    def audit(self, action_type: str, details: dict, success: bool = True):
        """
        Log security-critical actions
        
        Args:
            action_type: Type of action (e.g., 'file_access', 'command_execution')
            details: Dictionary with action details
            success: Whether action succeeded
        """
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action_type,
            "success": success,
            "details": details
        }
        
        # Write to JSONL audit log
        with open(self.audit_log, 'a', encoding='utf-8') as f:
            f.write(json.dumps(audit_entry) + '\n')
        
        # Also log to main logger
        level = "INFO" if success else "WARNING"
        self.logger.log(level, f"AUDIT: {action_type} - {details}")
    
    def command_executed(self, command: str, result: str, success: bool):
        """Log command execution"""
        self.audit("command_execution", {
            "command": command,
            "result": result[:200],  # Limit result length
            "success": success
        }, success)
    
    def file_accessed(self, filepath: str, operation: str, success: bool):
        """Log file access"""
        self.audit("file_access", {
            "file": filepath,
            "operation": operation,
            "success": success
        }, success)
    
    def app_controlled(self, app_name: str, action: str, success: bool):
        """Log application control"""
        self.audit("app_control", {
            "app": app_name,
            "action": action,
            "success": success
        }, success)
    
    def conversation_turn(self, user_input: str, assistant_response: str):
        """Log conversation turn"""
        if self.config.LOG_ALL_ACTIONS:
            self.audit("conversation", {
                "user": user_input[:100],
                "assistant": assistant_response[:100]
            })
    
    def security_event(self, event_type: str, details: dict):
        """Log security-related events"""
        self.audit(f"security_{event_type}", details, success=False)
        self.logger.warning(f"🔒 SECURITY: {event_type} - {details}")


# Convenience functions
def get_logger():
    """Get the logger instance"""
    return logger


if __name__ == "__main__":
    # Test logger
    from config.config import config
    nova_logger = NovaLogger(config)
    
    logger.info("NOVA Logger initialized")
    logger.debug("Debug message")
    logger.warning("Warning message")
    logger.error("Error message")
    
    # Test audit logging
    nova_logger.audit("test_action", {"param": "value"}, True)
    nova_logger.command_executed("echo test", "test", True)
