"""
NOVA Desktop Automation (Phase 6)
==================================
Enterprise desktop control and automation
"""

import time
from loguru import logger
from typing import Tuple, Optional, List
import subprocess


class DesktopAutomator:
    """
    Enterprise desktop automation system
    Control mouse, keyboard, windows, and UI elements
    """
    
    def __init__(self, config):
        self.config = config
        self.pyautogui = None
        self.keyboard = None
        self.mouse = None
        
        self._init_automation_libs()
        
        logger.info("Desktop automator initialized")
    
    def _init_automation_libs(self):
        """Initialize automation libraries"""
        try:
            import pyautogui
            self.pyautogui = pyautogui
            # Safety: add pause between actions
            pyautogui.PAUSE = 0.5
            logger.info("✓ PyAutoGUI loaded")
        except ImportError:
            logger.warning("PyAutoGUI not available")
        
        try:
            import keyboard
            self.keyboard = keyboard
            logger.info("✓ Keyboard library loaded")
        except ImportError:
            logger.warning("Keyboard library not available")
        
        try:
            import mouse
            self.mouse = mouse
            logger.info("✓ Mouse library loaded")
        except ImportError:
            logger.warning("Mouse library not available")
    
    # ==================== MOUSE CONTROL ====================
    
    def click(self, x: int = None, y: int = None, button: str = 'left', clicks: int = 1):
        """Click at coordinates or current position"""
        if not self.pyautogui:
            raise Exception("PyAutoGUI not available")
        
        if x is not None and y is not None:
            self.pyautogui.click(x, y, clicks=clicks, button=button)
            logger.info(f"Clicked at ({x}, {y})")
        else:
            self.pyautogui.click(clicks=clicks, button=button)
            logger.info(f"Clicked at current position")
    
    def move_mouse(self, x: int, y: int, duration: float = 0.5):
        """Move mouse to coordinates"""
        if not self.pyautogui:
            raise Exception("PyAutoGUI not available")
        
        self.pyautogui.moveTo(x, y, duration=duration)
        logger.info(f"Moved mouse to ({x}, {y})")
    
    def drag_mouse(self, x: int, y: int, duration: float = 0.5):
        """Drag mouse to coordinates"""
        if not self.pyautogui:
            raise Exception("PyAutoGUI not available")
        
        self.pyautogui.dragTo(x, y, duration=duration, button='left')
        logger.info(f"Dragged to ({x}, {y})")
    
    def scroll(self, amount: int):
        """Scroll (positive = up, negative = down)"""
        if not self.pyautogui:
            raise Exception("PyAutoGUI not available")
        
        self.pyautogui.scroll(amount)
        logger.info(f"Scrolled {amount}")
    
    # ==================== KEYBOARD CONTROL ====================
    
    def type_text(self, text: str, interval: float = 0.05):
        """Type text"""
        if not self.pyautogui:
            raise Exception("PyAutoGUI not available")
        
        self.pyautogui.write(text, interval=interval)
        logger.info(f"Typed text ({len(text)} chars)")
    
    def press_key(self, key: str, presses: int = 1):
        """Press a key"""
        if not self.pyautogui:
            raise Exception("PyAutoGUI not available")
        
        for _ in range(presses):
            self.pyautogui.press(key)
        logger.info(f"Pressed '{key}' {presses} time(s)")
    
    def hotkey(self, *keys):
        """Press hotkey combination (e.g., 'ctrl', 'c')"""
        if not self.pyautogui:
            raise Exception("PyAutoGUI not available")
        
        self.pyautogui.hotkey(*keys)
        logger.info(f"Pressed hotkey: {'+'.join(keys)}")
    
    # ==================== SCREEN OPERATIONS ====================
    
    def screenshot(self, region: Tuple[int, int, int, int] = None, filepath: str = None):
        """Take screenshot"""
        if not self.pyautogui:
            raise Exception("PyAutoGUI not available")
        
        if region:
            screenshot = self.pyautogui.screenshot(region=region)
        else:
            screenshot = self.pyautogui.screenshot()
        
        if filepath:
            screenshot.save(filepath)
            logger.info(f"Screenshot saved to {filepath}")
            return filepath
        else:
            logger.info("Screenshot taken")
            return screenshot
    
    def find_on_screen(self, image_path: str, confidence: float = 0.8):
        """Find image on screen"""
        if not self.pyautogui:
            raise Exception("PyAutoGUI not available")
        
        try:
            location = self.pyautogui.locateOnScreen(image_path, confidence=confidence)
            if location:
                logger.info(f"Image found at {location}")
                return location
            else:
                logger.info("Image not found on screen")
                return None
        except Exception as e:
            logger.error(f"Error finding image: {e}")
            return None
    
    def get_pixel_color(self, x: int, y: int) -> Tuple[int, int, int]:
        """Get RGB color of pixel at coordinates"""
        if not self.pyautogui:
            raise Exception("PyAutoGUI not available")
        
        color = self.pyautogui.pixel(x, y)
        logger.info(f"Pixel at ({x}, {y}): {color}")
        return color
    
    def get_screen_size(self) -> Tuple[int, int]:
        """Get screen resolution"""
        if not self.pyautogui:
            raise Exception("PyAutoGUI not available")
        
        size = self.pyautogui.size()
        return size.width, size.height
    
    # ==================== WINDOW MANAGEMENT ====================
    
    def minimize_window(self):
        """Minimize current window"""
        self.hotkey('win', 'down')
        logger.info("Minimized window")
    
    def maximize_window(self):
        """Maximize current window"""
        self.hotkey('win', 'up')
        logger.info("Maximized window")
    
    def close_window(self):
        """Close current window"""
        self.hotkey('alt', 'f4')
        logger.info("Closed window")
    
    def switch_window(self):
        """Switch to next window"""
        self.hotkey('alt', 'tab')
        logger.info("Switched window")
    
    # ==================== AUTOMATION SEQUENCES ====================
    
    def fill_form(self, fields: List[Tuple[str, str]]):
        """
        Fill form fields
        fields: [(field_value, tab_after), ...]
        """
        for value, tab_after in fields:
            self.type_text(value)
            if tab_after:
                self.press_key('tab')
            time.sleep(0.3)
        
        logger.info(f"Filled {len(fields)} form fields")
    
    def copy_paste(self, text: str = None):
        """Copy selection or paste text"""
        if text:
            # Paste text
            import pyperclip
            pyperclip.copy(text)
            self.hotkey('ctrl', 'v')
            logger.info("Pasted text")
        else:
            # Copy selection
            self.hotkey('ctrl', 'c')
            time.sleep(0.2)
            import pyperclip
            content = pyperclip.paste()
            logger.info(f"Copied: {content[:50]}...")
            return content
    
    def select_all(self):
        """Select all"""
        self.hotkey('ctrl', 'a')
        logger.info("Selected all")
    
    # ==================== ADVANCED AUTOMATION ====================
    
    def create_workflow(self, actions: List[Dict]):
        """
        Execute a workflow sequence
        
        actions: [
            {"action": "click", "x": 100, "y": 200},
            {"action": "type", "text": "Hello"},
            {"action": "press", "key": "enter"},
            ...
        ]
        """
        for i, action in enumerate(actions):
            action_type = action.get('action')
            
            logger.info(f"Workflow step {i+1}: {action_type}")
            
            if action_type == 'click':
                self.click(action.get('x'), action.get('y'))
            elif action_type == 'type':
                self.type_text(action.get('text'))
            elif action_type == 'press':
                self.press_key(action.get('key'))
            elif action_type == 'hotkey':
                self.hotkey(*action.get('keys'))
            elif action_type == 'wait':
                time.sleep(action.get('seconds', 1))
            
            time.sleep(0.5)  # Pause between actions
        
        logger.info(f"Workflow completed ({len(actions)} steps)")
    
    def record_workflow(self, duration: int = 10) -> List[Dict]:
        """
        Record user actions for future replay
        (Basic implementation - tracks clicks and keys)
        """
        logger.info(f"Recording workflow for {duration} seconds...")
        
        recorded_actions = []
        start_time = time.time()
        
        # This is a simplified version
        # Full implementation would hook into system events
        
        logger.warning("Workflow recording not fully implemented yet")
        return recorded_actions


class WindowsAutomator:
    """Windows-specific automation using UI Automation"""
    
    def __init__(self):
        try:
            import pywinauto
            self.pywinauto = pywinauto
            logger.info("✓ PyWinAuto loaded")
        except ImportError:
            logger.warning("PyWinAuto not available")
            self.pywinauto = None
    
    def get_window(self, title: str):
        """Get window by title"""
        if not self.pywinauto:
            raise Exception("PyWinAuto not available")
        
        app = self.pywinauto.Application().connect(title_re=f".*{title}.*")
        return app
    
    def list_windows(self) -> List[str]:
        """List all open windows"""
        if not self.pywinauto:
            raise Exception("PyWinAuto not available")
        
        from pywinauto import Desktop
        windows = Desktop(backend="uia").windows()
        return [w.window_text() for w in windows if w.window_text()]


if __name__ == "__main__":
    # Test desktop automation
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from config.config import config
    
    automator = DesktopAutomator(config)
    
    # Test basic operations
    print("Testing desktop automation...")
    
    # Get screen size
    width, height = automator.get_screen_size()
    print(f"Screen size: {width}x{height}")
    
    # Test workflow
    workflow = [
        {"action": "wait", "seconds": 1},
        {"action": "type", "text": "NOVA automation test"},
    ]
    
    print("Running test workflow...")
    automator.create_workflow(workflow)
    
    print("✓ Desktop automation ready!")
