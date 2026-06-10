"""
Windows-compatible actions module.
Replaces macOS Quartz/CoreGraphics with pyautogui and Windows APIs.
"""
import logging
import asyncio
import time
import pyautogui
from typing import Optional

logger = logging.getLogger(__name__)

# Configure pyautogui for faster operations
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.01


def _get_screen_size():
    """Return (width, height) of the screen in pixels."""
    return pyautogui.size()


async def flash_click_highlight(x, y, radius=16, duration=1.0):
    """Visual feedback for click (simplified version for Windows)."""
    # Note: Full visual highlighting would require tkinter or similar
    # This is a placeholder that could be enhanced with a simple overlay
    pass


async def _click_at_position(x, y, button='left'):
    """
    Perform a click at (x, y) using pyautogui.
    `button` can be 'left' or 'right'.
    """
    # Create async task for visual feedback (if implemented)
    asyncio.create_task(flash_click_highlight(x, y))
    
    # Move to position and click
    pyautogui.click(x=x, y=y, button=button)


async def left_click_pixel(position) -> bool:
    """Left-click the specified position."""
    screen_w, screen_h = _get_screen_size()
    
    # Handle both normalized (0-1000) and absolute coordinates
    if position[0] > 1 and position[1] > 1:
        abs_x = position[0] / 1000 * screen_w
        abs_y = position[1] / 1000 * screen_h
    else:
        abs_x = position[0] * screen_w
        abs_y = position[1] * screen_h
    
    try:
        await _click_at_position(abs_x, abs_y, button='left')
        logger.debug(f'✅ Successfully left-clicked pixel at absolute [{abs_x}, {abs_y}]')
        return True
    except Exception as e:
        logger.error(f'❌ Left click failed: {str(e)}')
        return False


async def right_click_pixel(position) -> bool:
    """Right-click the specified position."""
    screen_w, screen_h = _get_screen_size()
    
    # Handle both normalized (0-1000) and absolute coordinates
    if position[0] > 1 and position[1] > 1:
        abs_x = position[0] / 1000 * screen_w
        abs_y = position[1] / 1000 * screen_h
    else:
        abs_x = position[0] * screen_w
        abs_y = position[1] * screen_h
    
    try:
        await _click_at_position(abs_x, abs_y, button='right')
        logger.debug(f'✅ Successfully right-clicked pixel at absolute [{abs_x}, {abs_y}]')
        return True
    except Exception as e:
        logger.error(f'❌ Right click failed: {str(e)}')
        return False


async def move_to(position) -> bool:
    """Move the mouse cursor to the specified position."""
    screen_w, screen_h = _get_screen_size()
    
    # Handle both normalized (0-1000) and absolute coordinates
    if position[0] > 1 and position[1] > 1:
        abs_x = position[0] / 1000 * screen_w
        abs_y = position[1] / 1000 * screen_h
    else:
        abs_x = position[0] * screen_w
        abs_y = position[1] * screen_h
    
    try:
        pyautogui.moveTo(abs_x, abs_y, duration=0.1)
        logger.debug(f'✅ Successfully moved cursor to absolute [{abs_x}, {abs_y}]')
        return True
    except Exception as e:
        logger.error(f'❌ Move failed: {str(e)}')
        return False


async def drag_pixel(start, end, duration=0.5) -> bool:
    """Drag from start position to end position."""
    screen_w, screen_h = _get_screen_size()
    
    # Handle both normalized (0-1000) and absolute coordinates
    if start[0] > 1 and start[1] > 1 and end[0] > 1 and end[1] > 1:
        x1 = start[0] / 1000 * screen_w
        y1 = start[1] / 1000 * screen_h
        x2 = end[0] / 1000 * screen_w
        y2 = end[1] / 1000 * screen_h
    else:
        x1 = start[0] * screen_w
        y1 = start[1] * screen_h
        x2 = end[0] * screen_w
        y2 = end[1] * screen_h
    
    try:
        pyautogui.drag(x2 - x1, y2 - y1, duration=duration, start=(x1, y1))
        logger.debug(f'✅ Successfully dragged from [{x1}, {y1}] to [{x2}, {y2}]')
        return True
    except Exception as e:
        logger.error(f'❌ Drag failed: {str(e)}')
        return False


async def press(key: str = "enter") -> bool:
    """Press a single key using pyautogui."""
    try:
        pyautogui.press(key)
        logger.info(f"✅ Successfully pressed key: {key}")
        return True
    except Exception as e:
        logger.error(f"❌ Key press failed: {str(e)}")
        return False


async def type_into(text: str) -> bool:
    """Type text using pyautogui."""
    try:
        pyautogui.write(text, interval=0.02)
        logger.info("✅ Successfully typed the text!")
        return True
    except Exception as e:
        logger.error(f"❌ Type failed: {str(e)}")
        return False


async def press_combination(key1: str, key2: str, key3: Optional[str] = None) -> bool:
    """Press a combination of keys (e.g., Ctrl + Shift + S)."""
    try:
        if key3 is not None:
            pyautogui.hotkey(key1, key2, key3)
            logger.info(f"✅ Successfully pressed the combination: {key1} + {key2} + {key3}")
        else:
            pyautogui.hotkey(key1, key2)
            logger.info(f"✅ Successfully pressed the combination: {key1} + {key2}")
        return True
    except Exception as e:
        logger.error(f"❌ Key combination failed: {str(e)}")
        return False


async def _scroll_invisible(lines=1):
    """Scroll by specified number of lines."""
    direction = 1 if lines > 0 else -1
    for _ in range(abs(lines)):
        pyautogui.scroll(direction)
        await asyncio.sleep(0.003)
        if _ == 25:
            break


async def _scroll_invisible_at_position(x, y, lines):
    """
    Move cursor to (x, y), scroll by `lines` lines, then return.
    Positive lines = scroll up, negative = scroll down.
    """
    screen_w, screen_h = _get_screen_size()
    
    # Convert normalized coordinates to absolute
    abs_x = (x / 1000.0) * screen_w
    abs_y = (y / 1000.0) * screen_h
    
    # Move to position
    pyautogui.moveTo(abs_x, abs_y, duration=0.05)
    
    # Scroll
    await _scroll_invisible(lines)
    
    return True


async def scroll_up(amount: int) -> bool:
    """Scroll up by specified amount."""
    if amount > 25:
        amount = 25
    await _scroll_invisible(lines=amount)
    logger.info(f"✅ Successfully scrolled up by {amount} lines!")
    return True


async def scroll_down(amount: int) -> bool:
    """Scroll down by specified amount."""
    if amount > 25:
        amount = 25
    await _scroll_invisible(lines=-amount)
    logger.info(f"✅ Successfully scrolled down by {amount} lines!")
    return True
