import os

# Chatbot config path
home_dir = os.path.expanduser("~")
root_dir = os.path.join(home_dir, "xanylabeling_data/chatbot")
MODELS_CONFIG_PATH = os.path.join(root_dir, "models.json")
SETTINGS_CONFIG_PATH = os.path.join(root_dir, "settings.json")
PROVIDERS_CONFIG_PATH = os.path.join(root_dir, "providers.json")

# Global design system
ANIMATION_DURATION = "200ms"
BORDER_RADIUS = "8px"
FONT_FAMILY = "SF Pro Text, -apple-system, BlinkMacSystemFont, Helvetica Neue, Arial, sans-serif"
FONT_SIZE_TINY = "9px"
FONT_SIZE_SMALL = "11px"
FONT_SIZE_NORMAL = "13px"
FONT_SIZE_LARGE = "16px"
ICON_SIZE_NORMAL = (32, 32)
ICON_SIZE_SMALL = (16, 16)

# Initialization parameters
DEFAULT_WINDOW_TITLE = "Chatbot (Beta)"
DEFAULT_WINDOW_SIZE = (1200, 700)  # (w, h)
DEFAULT_PROVIDER = "ollama"
DEFAULT_FIXED_HEIGHT = 32
CHAT_PANEL_PERCENTAGE = 88
INPUT_PANEL_PERCENTAGE = 12
MIN_MSG_INPUT_HEIGHT = 20
MAX_MSG_INPUT_HEIGHT = 300
USER_MESSAGE_MAX_WIDTH_PERCENT = 70
DEFAULT_TEMPERATURE_VALUE = 1
TEMPERATURE_SLIDER_HEIGHT = 20

# Theme configuration
THEME = {
    "primary": "#60A5FA",               # Tailwind CSS blue-500
    "background": "#FFFFFF",            # Clean white background
    "background_secondary": "#F9F9F9",  # Light gray background
    "background_hover": "#DBDBDB",     # Light gray for hover
    "border": "#E5E5E5",                # Subtle border color
    "text": "#2C2C2E",                  # Dark gray for better readability
    "highlight_text": "#2196F3",        # Highlight text color
    "success": "#30D158",               # Softer green
    "warning": "#FF9F0A",               # Warm orange
    "error": "#FF453A",                 # Refined red
}
