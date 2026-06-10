"""
Windows-compatible controller service.
Replaces macOS-specific implementations with Windows equivalents using:
- pyautogui for mouse/keyboard control
- pygetwindow for window management
- ctypes for Windows API calls
"""
import asyncio
import logging
from typing import Optional
import subprocess
import time

from src.agent.views import ActionModel, ActionResult
from src.controller.registry.service import Registry
from src.controller.views import (
    InputTextAction,
    OpenAppAction,
    AppleScriptAction,
    PressAction,
    PressCombinedAction,
    DragAction,
    RightClickPixel,
    LeftClickPixel,
    ScrollDownAction,
    ScrollUpAction,
    MoveToAction,
    RecordAction
)

from src.windows.actions import type_into, press, _scroll_invisible_at_position, move_to, left_click_pixel, right_click_pixel, press_combination, drag_pixel
from src.windows.tree import WindowsUITreeBuilder
from src.utils import time_execution_async, time_execution_sync

from pypinyin import pinyin, Style

import re
import ctypes
from ctypes import wintypes
from rapidfuzz import process as rapidfuzz_process
from rapidfuzz import fuzz as rapidfuzz_fuzz

logger = logging.getLogger(__name__)

# Windows API constants
ENUM_WINDOWS_CALLBACK = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

def get_window_pid(hwnd):
    """Get process ID from window handle."""
    pid = wintypes.DWORD()
    ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return pid.value

def get_window_title(hwnd):
    """Get window title from handle."""
    length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
    buff = ctypes.create_unicode_buffer(length + 1)
    ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
    return buff.value

def is_window_visible(hwnd):
    """Check if window is visible."""
    return bool(ctypes.windll.user32.IsWindowVisible(hwnd))

def enum_windows_callback_factory(window_list):
    """Create callback for EnumWindows."""
    def callback(hwnd, lparam):
        if is_window_visible(hwnd):
            window_list.append(hwnd)
        return True
    return ENUM_WINDOWS_CALLBACK(callback)

def get_all_window_pids():
    """Get all PIDs with visible windows."""
    windows = []
    callback = enum_windows_callback_factory(windows)
    ctypes.windll.user32.EnumWindows(callback, None)
    
    pids = set()
    for hwnd in windows:
        pid = get_window_pid(hwnd)
        pids.add(pid)
    return pids

def fuzzy_find_pid(user_norm: str, workspace=None) -> Optional[int]:
    """
    Return a PID for the best matching running app (with visible window),
    or None if no good match found.
    """
    # Get all PIDs with visible windows
    visible_pids = get_all_window_pids()
    logger.debug(f"Visible PIDs: {visible_pids}")
    
    if not visible_pids:
        logger.debug("No candidate apps found.")
        return None
    
    # Build candidate map from window titles
    candidate_map = {}
    windows = []
    callback = enum_windows_callback_factory(windows)
    ctypes.windll.user32.EnumWindows(callback, None)
    
    for hwnd in windows:
        pid = get_window_pid(hwnd)
        title = get_window_title(hwnd)
        
        if title:
            norm_title = normalize_for_matching(title)
            if norm_title:
                key = f"{norm_title}:{pid}"
                candidate_map[key] = (pid, title)
    
    if not candidate_map:
        logger.debug("No candidate apps found with titles.")
        return None
    
    # Try ratio matching first
    ratio_match = rapidfuzz_process.extractOne(
        user_norm,
        candidate_map.keys(),
        scorer=rapidfuzz_fuzz.ratio
    )
    
    best_candidate_key = None
    best_confidence = 0
    
    if ratio_match:
        tmp_key, tmp_conf, _ = ratio_match
        logger.debug(f"Ratio best match: '{user_norm}' -> '{tmp_key}' (conf={tmp_conf})")
        if tmp_conf >= 80:
            best_candidate_key, best_confidence = tmp_key, tmp_conf
        else:
            logger.debug("Ratio confidence too low, falling back to partial_ratio.")
    else:
        logger.debug("No match using ratio, falling back to partial_ratio.")
    
    # Fallback to partial_ratio
    if not best_candidate_key:
        partial_match = rapidfuzz_process.extractOne(
            user_norm,
            candidate_map.keys(),
            scorer=rapidfuzz_fuzz.partial_ratio
        )
        if not partial_match:
            logger.debug("No fuzzy matches using partial_ratio either.")
            return None
        best_candidate_key, best_confidence, _ = partial_match
        logger.debug(
            f"Partial best match: '{user_norm}' -> '{best_candidate_key}' (conf={best_confidence})"
        )
    
    # Final check for confidence
    if best_confidence < 80:
        logger.debug(f"Best confidence only {best_confidence}, returning None.")
        return None
    
    # Get the (pid, title)
    pid, title = candidate_map[best_candidate_key]
    
    logger.info(
        f"Using best fuzzy match => PID: {pid}, "
        f"Title: {title}, "
        f"confidence={best_confidence}"
    )
    return pid


def chinese_to_pinyin(s: str) -> str:
    # Convert each character to pinyin, no tones, join with space
    return " ".join(syll[0] for syll in pinyin(s, style=Style.NORMAL))

def normalize_for_matching(s: str) -> str:
    # If it has Chinese, convert to pinyin
    if re.search(r"[\u4e00-\u9fff]", s):
        s = chinese_to_pinyin(s)
    # Lowercase, remove punctuation/spaces
    s = s.lower()
    s = re.sub(r"[^\w]", "", s)
    return s

def has_app_windows(pid: int) -> bool:
    """Check if a process has visible windows."""
    visible_pids = get_all_window_pids()
    return pid in visible_pids


class Controller:
    def __init__(
        self,
        exclude_actions: list[str] = [],
    ):
        self.exclude_actions = exclude_actions
        self.registry = Registry(exclude_actions)
        self._register_default_actions()
        self.win_tree_builder = WindowsUITreeBuilder()

    def _register_default_actions(self):
        """Register all default cua actions"""

        @self.registry.action(
                'Complete task',
                param_model=NoParamsAction)
        async def done():
            return ActionResult(extracted_content='done', is_done=True)
            
        @self.registry.action(
                'Type', 
                param_model=InputTextAction,
                requires_mac_builder=False)
        async def input_text(text: str):
            try:			
                input_successful = await type_into(text)
                if input_successful:
                    return ActionResult(extracted_content=f'Successfully input text')
                else:
                    msg = f'❌ Input failed'
                    return ActionResult(extracted_content=msg, error=msg)
            except Exception as e:
                msg = f'❌ An error occurred: {str(e)}'
                logging.error(msg)
                return ActionResult(extracted_content=msg, error=msg)


        @self.registry.action("Open a windows app", param_model=OpenAppAction)
        async def open_app(app_name: str):
            """
            Attempt to open a Windows app by name using start command.
            """
            user_input = app_name
            logger.info(f"\nLaunching app: {user_input}...")

            try:
                # Use Windows start command to launch application
                result = subprocess.run(
                    ['start', '""', user_input],
                    shell=True,
                    capture_output=True,
                    text=True
                )
                
                # Wait a bit for the app to launch
                await asyncio.sleep(1.0)
                
                # Try to find the PID
                pid = fuzzy_find_pid(normalize_for_matching(user_input))
                
                success_msg = f"✅ Launched {user_input}, PID={pid}"
                logger.info(success_msg)
                return ActionResult(extracted_content=success_msg, current_app_pid=pid)
                
            except Exception as e:
                error_msg = f"❌ Failed to launch '{user_input}': {str(e)}"
                logger.error(error_msg)
                return ActionResult(extracted_content=error_msg, error=error_msg)
        
        @self.registry.action(
            'Run PowerShell script',
            param_model=AppleScriptAction
        )
        async def run_powershell_script(script: str):
            """Run a PowerShell script (Windows equivalent of AppleScript)."""
            logger.debug(f'Running PowerShell script: {script}')
            
            try:
                result = subprocess.run(
                    ['powershell', '-Command', script],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    output = result.stdout.strip()
                    if output:
                        return ActionResult(extracted_content=output)
                    else:
                        return ActionResult(extracted_content="Success")
                else:
                    error_msg = f"PowerShell failed with return code {result.returncode}: {result.stderr.strip()}"
                    logger.error(error_msg)
                    return ActionResult(extracted_content=error_msg, error=error_msg)
                    
            except Exception as e:
                error_msg = f"Failed to run PowerShell script: {str(e)}"
                logger.error(error_msg)
                return ActionResult(extracted_content=error_msg, error=error_msg)
        
        @self.registry.action(
            'Single Hotkey',
            param_model=PressAction,
        )
        async def Hotkey(key: str = "enter"):
            # The key is Key.enter, but what i need is the string "enter"
            key_press = key.replace("Key.", "")
            press_successful = await press(key_press)
            if press_successful:
                logging.info(f'✅ pressed key code: {key}')
                return ActionResult(extracted_content=f'Successfully press keyboard with key code {key}')
            
        @self.registry.action(
            'Press Multiple Hotkey',
            param_model=PressCombinedAction,
        )
        async def multi_Hotkey(key1: str, key2: str, key3: Optional[str] = None):
            def clean_key(raw: str | None) -> str | None:
                """Strip the `Key.` prefix and any stray quote marks."""
                if raw is None:
                    return None
                return raw.replace("Key.", "").strip("'\"")   # handles 't', "t", Key.'t', etc.
            key1 = clean_key(key1)
            key2 = clean_key(key2)
            key3 = clean_key(key3)
            key_map = {
                'cmd': 'win',
                'win': 'win',
                'delete': 'backspace'
            }
            # Map key names
            def map_key(key: str) -> str:
                return key_map.get(key.lower(), key)
            
            key1 = map_key(key1)
            key2 = map_key(key2)
            key3 = map_key(key3) if key3 is not None else None
            if key3 is not None:
                press_successful = await press_combination(key1, key2, key3)
                if press_successful:
                    logging.info(f'✅ pressed combination key: {key1}, {key2} and {key3}')
                return ActionResult(extracted_content=f'Successfully press keyboard with key code {key1}, {key2} and {key3}')
            else:
                press_successful = await press_combination(key1,key2,key3=None)
                if press_successful:
                    logging.info(f'✅ pressed combination key: {key1} and {key2}')
                return ActionResult(extracted_content=f'Successfully press keyboard with key code {key1} and {key2}')

        @self.registry.action(
            'RightSingle click at specific pixel',
            param_model=RightClickPixel,
            requires_mac_builder=False
        )
        async def RightSingle(position: list = [0,0]):
            logger.debug(f'Correct clicking pixel position {position}')
            try:
                click_successful = await right_click_pixel(position)
                if click_successful:
                    logging.info(f'✅ Finished right click at pixel: {position}')
                    return ActionResult(extracted_content=f'Successfully clicked pixel {position}')
                else:
                    msg = f'❌ Right click failed for pixel with position: {position}'
                    return ActionResult(extracted_content=msg, error=msg)
            except Exception as e:
                msg = f'❌ An error occurred: {str(e)}'
                logging.error(msg)
                return ActionResult(extracted_content=msg, error=msg)
            
        @self.registry.action(
            'Left click at specific pixel',
            param_model=LeftClickPixel,
            requires_mac_builder=False
        )
        async def Click(position: list = [0,0]):
            logger.debug(f'Correct clicking pixel position {position}')
            try:
                click_successful = await left_click_pixel(position)
                if click_successful:
                    logging.info(f'✅ Finished left click at pixel: {position}')
                    return ActionResult(extracted_content=f'Successfully clicked pixel {position}')
                else:
                    msg = f'❌ Left click failed for pixel with position: {position}'
                    return ActionResult(extracted_content=msg, error=msg)
            except Exception as e:
                msg = f'❌ An error occurred: {str(e)}'
                logging.error(msg)
                return ActionResult(extracted_content=msg, error=msg)
            
        @self.registry.action(
            'Drag an object from one pixel to another',
            param_model=DragAction,
            requires_mac_builder=False
        )
        async def Drag(position1: list = [0,0], position2: list = [0,0]):
            try:
                drag_successful = await drag_pixel(position1, position2)
                if drag_successful:
                    logger.info(f'Correct draging pixel from position {position1} to {position2}')
                    return ActionResult(extracted_content=f'Successfully drag pixel {position1} to {position2}')
                else:
                    msg = f'❌ Drag failed for pixel with position: {position1}'
                    return ActionResult(extracted_content=msg, error=msg)
            except Exception as e:
                msg = f'❌ An error occurred: {str(e)}'
                logging.error(msg)
                return ActionResult(extracted_content=msg, error=msg)
            
        @self.registry.action(
                'Move mouse to specific pixel',
                param_model=MoveToAction,
                requires_mac_builder=False
        )
        async def move_mouse(position: list = [0,0]):
            logger.debug(f'Correct move mouse to position {position}')
            try:
                move_successful = await move_to(position)
                if move_successful:
                    logging.info(f'✅ Finished move mouse to pixel: {position}')
                    return ActionResult(extracted_content=f'Successfully move mouse to {position}')
                else:
                    msg = f'❌ Failed move mouse to pixel with position: {position}'
                    return ActionResult(extracted_content=msg, error=msg)
            except Exception as e:
                msg = f'❌ An error occurred: {str(e)}'
                logging.error(msg)
                return ActionResult(extracted_content=msg, error=msg)
        
        @self.registry.action(
            'Scroll up',
            param_model=ScrollUpAction,
        )
        async def scroll_up(position, dx: int = -25, dy: int = 25):
            x,y = position
            amount = dy
            scroll_successful = await _scroll_invisible_at_position(x,y,amount)
            if scroll_successful:
                logging.info(f'✅ Scrolled up by {amount}')
                return ActionResult(extracted_content=f'Successfully scrolled up by {amount}')
            
        @self.registry.action(
            'Scroll down',
            param_model=ScrollDownAction,
        )
        async def scroll_down(position, dx: int = -25, dy: int = 25):
            x,y = position
            amount = dy
            scroll_successful = await _scroll_invisible_at_position(x,y, -amount)
            if scroll_successful:
                logging.info(f'✅ Scrolled down by {amount}')
                return ActionResult(extracted_content=f'Successfully scrolled down by {amount}')
            
        @self.registry.action(
            'Tell the short memory that you are recording information',
            param_model=RecordAction,
        )
        async def record_info(text: str, file_name: str):
            return ActionResult(extracted_content=f'{file_name}: {text}')
        
        @self.registry.action(
            'Wait',
            param_model=NoParamsAction
        )
        async def wait():
            return ActionResult(extracted_content=f'Waiting')

    def action(self, description: str, **kwargs):
        """Decorator for registering custom actions

        @param description: Describe the LLM what the function does (better description == better function calling)
        """
        return self.registry.action(description, **kwargs)

    @time_execution_async('--multi-act')
    async def multi_act(
        self, actions: list[ActionModel], win_tree_builder: WindowsUITreeBuilder, action_valid: bool = True
    ) -> list[ActionResult]:
        """Execute multiple actions"""
        results = []
        if action_valid:
            for i, action in enumerate(actions):
                results.append(await self.act(action, win_tree_builder))
                await asyncio.sleep(0.5)

                logger.debug(f'Executed action {i + 1} / {len(actions)}')
                if results[-1].is_done or results[-1].error or i == len(actions) - 1:
                    break

            return results
        else:
            return [ActionResult(error="Invalid action, index is out of the UI Tree. Please use the screenshot to determine the correct pixel to act on.",include_in_memory=True)]

    @time_execution_sync('--act')
    async def act(self, action: ActionModel, win_tree_builder: WindowsUITreeBuilder) -> ActionResult:
        """Execute an action"""
        try:
            for action_name, params in action.model_dump(exclude_unset=True).items():
                if params is not None:
                    result = await self.registry.execute_action(action_name, params, win_tree_builder=win_tree_builder)
                    if isinstance(result, str):
                        return ActionResult(extracted_content=result)
                    elif isinstance(result, ActionResult):
                        return result
                    elif result is None:
                        return ActionResult()
                    else:
                        raise ValueError(f'Invalid action result type: {type(result)} of {result}')
            return ActionResult()
        except Exception as e:
            msg = f'Error executing action: {str(e)}'
            logger.error(msg)
            return ActionResult(extracted_content=msg, error=msg)

class NoParamsAction(ActionModel):
    """
    Simple parameter model requiring no arguments.
    """
    pass
