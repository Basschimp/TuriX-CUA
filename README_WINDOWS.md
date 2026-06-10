# Windows Setup Guide for TuriX-CUA with OpenRouter + Hermes

This guide explains how to run TuriX-CUA on Windows using OpenRouter with Hermes models.

## Prerequisites

1. **Python 3.10+** installed on Windows
2. **OpenRouter API Key** - Get one at https://openrouter.ai/keys

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements_windows.txt
```

Or install manually:

```bash
pip install pyautogui pygetwindow pymsgbox pytweening mouseinfo pywin32
pip install langchain-openai langchain-anthropic langchain-ollama pynput rapidfuzz pypinyin openai
```

### 2. Configure OpenRouter API Key

Set your OpenRouter API key as an environment variable:

```cmd
setx OPENAI_API_KEY "your_openrouter_api_key_here"
```

Or edit the config file directly and replace `your_openrouter_api_key_here` with your actual key.

## Configuration

The example configuration file `examples/config_windows_openrouter.json` is pre-configured for:
- **Provider**: OpenRouter
- **Model**: NousResearch Hermes 3 Llama 3.1 70B
- **Platform**: Windows

### Available Hermes Models on OpenRouter

You can use any of these Hermes models by changing the `model_name` in your config:

- `nousresearch/hermes-3-llama-3.1-70b` (Recommended)
- `nousresearch/hermes-3-llama-3.1-405b`
- `nousresearch/hermes-2-pro-llama-3-8b`
- `nousresearch/hermes-2-theta-llama-3-70b`

See full list at: https://openrouter.ai/models?q=hermes

### Configuration Options

Edit `examples/config_windows_openrouter.json`:

```json
{
  "brain_llm": {
    "provider": "openrouter",
    "model_name": "nousresearch/hermes-3-llama-3.1-70b",
    "api_key": "your_openrouter_api_key_here",
    "base_url": "https://openrouter.ai/api/v1",
    "supports_tool_calling": true,
    "supports_response_format": false
  },
  ...
}
```

## Running the Agent

### Basic Usage

```cmd
cd examples
python main_win.py -c config_windows_openrouter.json
```

### Custom Config

```cmd
python main_win.py -c path/to/your/config.json
```

## Key Differences from macOS Version

### 1. Controller Module
- Uses `src/controller/service_win.py` instead of `src/controller/service.py`
- Replaces macOS-specific APIs (Quartz, CoreGraphics, Cocoa) with Windows equivalents
- Uses `pyautogui` for mouse/keyboard control
- Uses `ctypes` for Windows API calls

### 2. Hotkey Configuration
- Changed default force-stop hotkey from `command+shift+2` to `ctrl+shift+2`
- The `command` key is automatically mapped to the Windows key

### 3. App Launching
- Uses Windows `start` command instead of macOS `NSWorkspace`
- PowerShell scripts instead of AppleScript

### 4. Window Management
- Uses Windows API via `ctypes` instead of macOS Accessibility APIs
- Fuzzy matching works on window titles

## Troubleshooting

### Screen Permissions
Windows doesn't require special screen recording permissions like macOS. However, ensure:
- Your terminal/IDE has necessary permissions if running in a restricted environment
- User Account Control (UAC) isn't blocking automation

### PyAutoGUI FailSafe
If you need to emergency-stop, move your mouse to the top-left corner (0, 0). 
PyAutoGUI's failsafe will raise an exception.

To disable failsafe (not recommended), set in code:
```python
pyautogui.FAILSAFE = False
```

### Common Issues

1. **"Module not found" errors**
   ```cmd
   pip install -r requirements_windows.txt
   ```

2. **"API key not valid"**
   - Check your OpenRouter API key is correct
   - Ensure it has sufficient credits

3. **"Access denied" for window operations**
   - Run terminal as Administrator
   - Check Windows Security settings

## Advanced Configuration

### Using Different Models

For brain/actor/planner/memory, you can mix different models:

```json
{
  "brain_llm": {
    "provider": "openrouter",
    "model_name": "nousresearch/hermes-3-llama-3.1-405b"
  },
  "actor_llm": {
    "provider": "openrouter",
    "model_name": "nousresearch/hermes-3-llama-3.1-70b"
  }
}
```

### Custom Base URL

If using a different provider that supports OpenAI-compatible API:

```json
{
  "provider": "openrouter",
  "base_url": "https://your-custom-api.com/v1"
}
```

### Adjusting Performance

```json
{
  "agent": {
    "max_actions_per_step": 3,
    "max_steps": 50,
    "memory_budget_tokens": 1000
  }
}
```

## File Structure

```
/workspace
├── examples/
│   ├── main_win.py                    # Windows entry point
│   ├── config_windows_openrouter.json # Example config for OpenRouter + Hermes
│   └── config.json                    # Original macOS config
├── src/
│   ├── controller/
│   │   ├── service.py                 # macOS controller
│   │   └── service_win.py             # Windows controller
│   └── windows/
│       ├── actions.py                 # Windows action implementations
│       └── tree.py                    # Windows UI tree builder
├── requirements_windows.txt           # Windows dependencies
└── README_WINDOWS.md                  # This file
```

## Additional Resources

- [OpenRouter Documentation](https://openrouter.ai/docs)
- [Hermes Models](https://huggingface.co/NousResearch)
- [PyAutoGUI Documentation](https://pyautogui.readthedocs.io/)
- [Original TuriX-CUA README](README.md)

## Support

For issues specific to the Windows implementation:
1. Check this guide first
2. Review error logs in `.turix_tmp/logging.log`
3. Open an issue on the repository
