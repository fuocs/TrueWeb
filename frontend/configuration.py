# COLORS
LINK_TEXT = "#007bff"
UNSAFE = "#be0000"
CAUTION = "#e68200"
TRUSTED = "#00aa00"

# Error/Warning colors for UI elements
ERROR_TEXT = "#ff4444"      # Red text for errors
ERROR_BG = "#ffcccc"        # Light red background
WARNING_TEXT = "#ff9800"    # Orange text for warnings
WARNING_BG = "#fff3cd"      # Light yellow background
REDIRECT_WARNING = "#ff6b6b"  # Red for redirect warnings

ACTIVE_GREEN = "#4CAF50"

# Google button colors
GOOGLE_BG_LIGHT = "#ffffff"
GOOGLE_TEXT_LIGHT = "#374151" 
GOOGLE_BORDER_LIGHT = "#d1d5db"

GOOGLE_BG_DARK = "#2d2d2d"    
GOOGLE_TEXT_DARK = "#e5e7eb"  
GOOGLE_BORDER_DARK = "#404040"

# Light mode
L_APP_BACKGROUND = "#e6ffc9"
L_HEADER_BACKGROUND = "#a7e75d"
L_HEADER_TITLE = "#013027"
L_NORMAL_TITLE = "#206035"
L_BUTTON_BACKGROUND = "#15803d"
L_DARK_TEXT = "#4c4c4c"      # Chữ màu đậm (dùng cho nền sáng)
L_LIGHT_TEXT = "#7c7c7c"     # Chữ màu nhạt (mô tả)
L_SHADOW = "#bde191"
L_BAR_BACKGROUND = "#fafff6"
L_WHITE = "#ffffff"    

L_CANCEL_BG = "#6b7280"      
L_CANCEL_HOVER = "#4b5563" 

L_SWITCH_ACTIVE = ACTIVE_GREEN  # Nền khi bật (Xanh lá)
L_SWITCH_INACTIVE = "#e0e0e0"   # Nền khi tắt (Xám nhạt)
L_KNOB_COLOR = "#ffffff"        # Màu nút tròn (Trắng)
L_KNOB_BORDER = "#d5d5d5"       # Viền nút tròn

L_ICON_COLOR = L_DARK_TEXT

# Preview/Image container colors (light mode)
L_PREVIEW_BG = "#f0f0f0"     # Light gray for preview backgrounds
L_BORDER_COLOR = "#ccc"      # Border color
L_IMAGE_BG = "#2c3e50"       # Dark blue-gray for image containers

# Dark mode
D_APP_BACKGROUND = "#013027"
D_HEADER_BACKGROUND = "#689350"
D_HEADER_TITLE = "#e6ffc9"
D_NORMAL_TITLE = "#a7e75d"
D_BUTTON_BACKGROUND = "#a7e75d"
D_DARK_TEXT = "#cecece"
D_LIGHT_TEXT = "#a0a0a0"     
D_SHADOW = "#1CA388"
D_BAR_BACKGROUND = "#1f2937"
D_WHITE = "#000000"

D_CANCEL_BG = "#374151"      # Xám tối (Gray-700) cho dịu mắt
D_CANCEL_HOVER = "#4b5563"

D_ICON_COLOR = D_DARK_TEXT

D_SWITCH_ACTIVE = ACTIVE_GREEN  # Nền khi bật (Vẫn là Xanh lá đó cho nổi)
D_SWITCH_INACTIVE = "#4a4a4a"   # Nền khi tắt (Xám đậm hơn nền container một chút)
D_KNOB_COLOR = "#dce0dd"        # Màu nút tròn (Trắng hơi xám để đỡ chói trên nền tối)
D_KNOB_BORDER = "#3e3e42"       # Viền nút tròn tối màu

# Preview/Image container colors (dark mode)
D_PREVIEW_BG = "#2d3748"     # Darker gray for preview backgrounds
D_BORDER_COLOR = "#4a5568"   # Darker border
D_IMAGE_BG = "#1a202c"       # Very dark blue-gray for image containers

# general colors, light mode by default
APP_BACKGROUND = L_APP_BACKGROUND
HEADER_BACKGROUND = L_HEADER_BACKGROUND
HEADER_TITLE = L_HEADER_TITLE
NORMAL_TITLE = L_NORMAL_TITLE
BUTTON_BACKGROUND = L_BUTTON_BACKGROUND
DARK_TEXT = L_DARK_TEXT
LIGHT_TEXT = L_LIGHT_TEXT
SHADOW_COLOR = L_SHADOW
BAR_BACKGROUND = L_BAR_BACKGROUND
WHITE = L_WHITE 
BLACK = L_DARK_TEXT

SWITCH_ACTIVE = L_SWITCH_ACTIVE
SWITCH_INACTIVE = L_SWITCH_INACTIVE
KNOB_COLOR = L_KNOB_COLOR
KNOB_BORDER = L_KNOB_BORDER

GOOGLE_BG = GOOGLE_BG_LIGHT
GOOGLE_TEXT = GOOGLE_TEXT_LIGHT
GOOGLE_BORDER = GOOGLE_BORDER_LIGHT

ICON_COLOR = L_ICON_COLOR

CANCEL_BG = L_CANCEL_BG
CANCEL_HOVER = L_CANCEL_HOVER

PREVIEW_BG = L_PREVIEW_BG
BORDER_COLOR = L_BORDER_COLOR
IMAGE_BG = L_IMAGE_BG

def set_mode(is_dark):
    global APP_BACKGROUND, HEADER_BACKGROUND, HEADER_TITLE, NORMAL_TITLE, WHITE, BLACK
    global BUTTON_BACKGROUND, DARK_TEXT, LIGHT_TEXT, SHADOW_COLOR, BAR_BACKGROUND
    global SWITCH_ACTIVE, SWITCH_INACTIVE, KNOB_COLOR, KNOB_BORDER
    global GOOGLE_BG, GOOGLE_TEXT, GOOGLE_BORDER
    global PREVIEW_BG, BORDER_COLOR, IMAGE_BG
    global ICON_COLOR
    global CANCEL_BG, CANCEL_HOVER

    if is_dark:
        APP_BACKGROUND = D_APP_BACKGROUND
        HEADER_BACKGROUND = D_HEADER_BACKGROUND
        HEADER_TITLE = D_HEADER_TITLE
        NORMAL_TITLE = D_NORMAL_TITLE
        BUTTON_BACKGROUND = D_BUTTON_BACKGROUND
        DARK_TEXT = D_DARK_TEXT
        LIGHT_TEXT = D_LIGHT_TEXT
        SHADOW_COLOR = D_SHADOW
        BAR_BACKGROUND = D_BAR_BACKGROUND

        WHITE = D_BAR_BACKGROUND
        BLACK = L_WHITE

        SWITCH_ACTIVE = D_SWITCH_ACTIVE
        SWITCH_INACTIVE = D_SWITCH_INACTIVE
        KNOB_COLOR = D_KNOB_COLOR
        KNOB_BORDER = D_KNOB_BORDER

        GOOGLE_BG = GOOGLE_BG_DARK
        GOOGLE_TEXT = GOOGLE_TEXT_DARK
        GOOGLE_BORDER = GOOGLE_BORDER_DARK

        ICON_COLOR = D_ICON_COLOR

        CANCEL_BG = D_CANCEL_BG
        CANCEL_HOVER = D_CANCEL_HOVER

        PREVIEW_BG = D_PREVIEW_BG
        BORDER_COLOR = D_BORDER_COLOR
        IMAGE_BG = D_IMAGE_BG

    else:
        APP_BACKGROUND = L_APP_BACKGROUND
        HEADER_BACKGROUND = L_HEADER_BACKGROUND
        HEADER_TITLE = L_HEADER_TITLE
        NORMAL_TITLE = L_NORMAL_TITLE
        BUTTON_BACKGROUND = L_BUTTON_BACKGROUND
        DARK_TEXT = L_DARK_TEXT
        LIGHT_TEXT = L_LIGHT_TEXT
        SHADOW_COLOR = L_SHADOW
        BAR_BACKGROUND = L_BAR_BACKGROUND

        WHITE = L_WHITE
        BLACK = L_DARK_TEXT
        
        SWITCH_ACTIVE = L_SWITCH_ACTIVE
        SWITCH_INACTIVE = L_SWITCH_INACTIVE
        KNOB_COLOR = L_KNOB_COLOR
        KNOB_BORDER = L_KNOB_BORDER

        GOOGLE_BG = GOOGLE_BG_LIGHT
        GOOGLE_TEXT = GOOGLE_TEXT_LIGHT
        GOOGLE_BORDER = GOOGLE_BORDER_LIGHT

        ICON_COLOR = L_ICON_COLOR

        CANCEL_BG = L_CANCEL_BG
        CANCEL_HOVER = L_CANCEL_HOVER

        PREVIEW_BG = L_PREVIEW_BG
        BORDER_COLOR = L_BORDER_COLOR
        IMAGE_BG = L_IMAGE_BG

# SIZING
REVIEW_CARD_WIDTH = 250
REVIEW_CARD_HEIGHT = 150

# APPLICATION SETTINGS
DEFAULT_TIMEOUT = 15  # Default timeout in seconds
DEFAULT_RETRY_COUNT = 3  # Default retry count for failed modules
_current_timeout = DEFAULT_TIMEOUT
_current_retry_count = DEFAULT_RETRY_COUNT

def get_timeout():
    """Get current timeout value"""
    return _current_timeout

def set_timeout(timeout):
    """Set timeout value (1-120 seconds)"""
    global _current_timeout
    _current_timeout = max(1, min(timeout, 120))  # Clamp between 1-120

def get_retry_count():
    """Get current retry count"""
    return _current_retry_count

def set_retry_count(retry_count):
    """Set retry count (0-5 retries)"""
    global _current_retry_count
    _current_retry_count = max(0, min(retry_count, 5))  # Clamp between 0-5