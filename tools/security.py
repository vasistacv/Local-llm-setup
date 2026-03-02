"""
NOVA Security Manager (Phase 8)
=================================
Enterprise-level security and permission system
"""

import json
from pathlib import Path
from datetime import datetime
from loguru import logger
from typing import Dict, Any, List, Optional
import hashlib


class SecurityManager:
    """
    Enterprise security manager
    - Permission gates
    - Action logging
    - Risk assessment
    - Command validation
    """
    
    def __init__(self, config):
        self.config = config
        self.audit_log = config.LOGS_DIR / "security_audit.jsonl"
        
        # Risk levels for different tools
        self.risk_levels = {
            # LOW RISK - Auto-allow
            "get_system_info": "low",
            "list_running_apps": "low",
            "search_file": "low",
            "read_file": "low",
            "read_pdf": "low",
            "open_url": "low",
            "search_web": "low",
            
            # MEDIUM RISK - Confirm if in safe mode
            "create_file": "medium",
            "create_folder": "medium",
            "create_document": "medium",
            "open_app": "medium",
            "move_file": "medium",
            
            # HIGH RISK - Always confirm
            "delete_file": "high",
            "close_app": "high",
            "run_command": "high",
        }
        
        # Dangerous command patterns
        self.dangerous_patterns = [
            "rm -rf", "del /f", "format", "shutdown", 
            "reboot", "reg delete", "rmdir /s",
            "taskkill /f", "net user", "net localgroup"
        ]
        
        logger.info("Security manager initialized")
    
    def can_execute(self, tool_name: str, parameters: Dict[str, Any]) -> bool:
        """
        Check if tool can be executed
        
        Returns:
            True if allowed, False otherwise
        """
        # Get risk level
        risk = self.risk_levels.get(tool_name, "medium")
        
        # LOW RISK - Always allow
        if risk == "low":
            return True
        
        # MEDIUM RISK - Check safe mode
        if risk == "medium":
            if self.config.SAFE_MODE:
                logger.warning(f"Medium-risk tool '{tool_name}' blocked by safe mode")
                return self._request_confirmation(tool_name, parameters, risk)
            return True
        
        # HIGH RISK - Always confirm
        if risk == "high":
            # Check for dangerous commands
            if tool_name == "run_command":
                command = parameters.get("command", "")
                if self._is_dangerous_command(command):
                    logger.error(f"🚨 DANGEROUS COMMAND BLOCKED: {command}")
                    return False
            
            if tool_name == "delete_file":
                path = parameters.get("path", "")
                if self._is_protected_path(path):
                    logger.error(f"🚨 PROTECTED PATH BLOCKED: {path}")
                    return False
            
            # Require confirmation
            if self.config.REQUIRE_CONFIRMATION:
                return self._request_confirmation(tool_name, parameters, risk)
        
        return True
    
    def _is_dangerous_command(self, command: str) -> bool:
        """Check if command contains dangerous patterns"""
        command_lower = command.lower()
        for pattern in self.dangerous_patterns:
            if pattern in command_lower:
                return True
        return False
    
    def _is_protected_path(self, path: str) -> bool:
        """Check if path is in protected locations"""
        path_obj = Path(path)
        
        for restricted in self.config.RESTRICTED_PATHS:
            try:
                if path_obj.is_relative_to(restricted):
                    return True
            except:
                continue
        
        return False
    
    def _request_confirmation(self, tool_name: str, parameters: Dict[str, Any], risk: str) -> bool:
        """
        Request user confirmation for risky actions
        In production, this would show a UI prompt
        For now, log and allow in non-safe mode
        """
        logger.warning(f"⚠️  {risk.upper()} RISK: {tool_name} with {parameters}")
        
        if self.config.SAFE_MODE:
            logger.error("Action blocked by safe mode")
            return False
        
        # In production: show confirmation dialog
        # For now: log and allow
        logger.warning("Action allowed (confirmation required in production)")
        return True
    
    def log_execution(self, tool_name: str, parameters: Dict[str, Any], 
                     success: bool, error: str = None):
        """Log tool execution to audit trail"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "tool": tool_name,
            "parameters": parameters,
            "success": success,
            "error": error,
            "risk_level": self.risk_levels.get(tool_name, "unknown")
        }
        
        # Write to audit log
        with open(self.audit_log, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + '\n')
        
        # Also log to main logger
        if success:
            logger.info(f"✓ Tool executed: {tool_name}")
        else:
            logger.error(f"✗ Tool failed: {tool_name} - {error}")
    
    def get_audit_log(self, limit: int = 100) -> List[Dict]:
        """Get recent audit log entries"""
        if not self.audit_log.exists():
            return []
        
        entries = []
        with open(self.audit_log, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entries.append(json.loads(line))
                except:
                    continue
        
        return entries[-limit:]  # Return last N entries
    
    def generate_audit_report(self) -> str:
        """Generate security audit report"""
        entries = self.get_audit_log()
        
        total = len(entries)
        successful = sum(1 for e in entries if e['success'])
        failed = total - successful
        
        high_risk = sum(1 for e in entries if e.get('risk_level') == 'high')
        
        report = f"""
========================================
SECURITY AUDIT REPORT
========================================
Total Actions: {total}
Successful: {successful}
Failed: {failed}
High-Risk Actions: {high_risk}

Recent High-Risk Actions:
"""
        for entry in reversed(entries):
            if entry.get('risk_level') == 'high':
                report += f"\n- {entry['timestamp']}: {entry['tool']} - {'✓' if entry['success'] else '✗'}"
        
        return report


class RateLimiter:
    """Rate limiting for tool execution"""
    
    def __init__(self, max_per_minute: int = 30):
        self.max_per_minute = max_per_minute
        self.calls = []
    
    def can_execute(self) -> bool:
        """Check if execution is allowed (not rate limited)"""
        now = datetime.now()
        
        # Remove old calls (older than 1 minute)
        self.calls = [c for c in self.calls if (now - c).seconds < 60]
        
        if len(self.calls) >= self.max_per_minute:
            logger.warning(f"Rate limit exceeded ({self.max_per_minute}/min)")
            return False
        
        self.calls.append(now)
        return True


class PermissionManager:
    """Advanced permission management"""
    
    def __init__(self, config):
        self.config = config
        self.permissions_file = config.CONFIG_DIR / "permissions.json"
        self.permissions = self._load_permissions()
    
    def _load_permissions(self) -> Dict:
        """Load permissions from file"""
        if self.permissions_file.exists():
            return json.loads(self.permissions_file.read_text())
        else:
            # Default permissions
            return {
                "owner": {
                    "can_execute_commands": True,
                    "can_delete_files": True,
                    "can_modify_system": True,
                },
                "guest": {
                    "can_execute_commands": False,
                    "can_delete_files": False,
                    "can_modify_system": False,
                },
            }
    
    def save_permissions(self):
        """Save permissions to file"""
        self.permissions_file.write_text(json.dumps(self.permissions, indent=2))
    
    def has_permission(self, user: str, permission: str) -> bool:
        """Check if user has specific permission"""
        user_perms = self.permissions.get(user, {})
        return user_perms.get(permission, False)


if __name__ == "__main__":
    # Test security manager
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from config.config import config
    
    security = SecurityManager(config)
    
    # Test various actions
    print("Testing security checks...")
    
    print("\n1. Low risk (should allow):")
    print(security.can_execute("get_system_info", {}))
    
    print("\n2. Medium risk (should allow if not safe mode):")
    print(security.can_execute("create_file", {"path": "test.txt"}))
    
    print("\n3. High risk (should require confirmation):")
    print(security.can_execute("delete_file", {"path": "test.txt"}))
    
    print("\n4. Dangerous command (should block):")
    print(security.can_execute("run_command", {"command": "rm -rf /"}))
    
    print("\n5. Protected path (should block):")
    print(security.can_execute("delete_file", {"path": "C:\\Windows\\system32\\test.dll"}))
    
    # Generate report
    print("\n" + security.generate_audit_report())
