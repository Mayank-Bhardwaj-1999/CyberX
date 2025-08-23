#!/usr/bin/env python3
"""
Unicode Helper for Windows Compatibility
Provides safe Unicode printing for Windows Command Prompt
"""

import sys
import os
import platform

def safe_print(*args, **kwargs):
    """
    Safe print function that handles Unicode characters on Windows
    Falls back to ASCII-safe alternatives when Unicode fails
    """
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # Convert Unicode emojis to ASCII alternatives
        safe_args = []
        for arg in args:
            if isinstance(arg, str):
                # Replace common Unicode emojis with ASCII alternatives
                safe_arg = (arg
                    .replace("✅", "[OK]")
                    .replace("❌", "[ERROR]")
                    .replace("⚠️", "[WARNING]")
                    .replace("🚀", "[START]")
                    .replace("📰", "[NEWS]")
                    .replace("🔄", "[CYCLE]")
                    .replace("📊", "[DATA]")
                    .replace("🤖", "[AI]")
                    .replace("⏰", "[TIME]")
                    .replace("🔔", "[ALERT]")
                    .replace("🌐", "[WEB]")
                    .replace("📦", "[BACKUP]")
                    .replace("🔧", "[SETUP]")
                    .replace("💡", "[INFO]")
                    .replace("🎯", "[TARGET]")
                    .replace("🛡️", "[SECURITY]")
                    .replace("📋", "[LIST]")
                    .replace("🗄️", "[ARCHIVE]")
                    .replace("🧪", "[TEST]")
                    .replace("📈", "[STATS]")
                    .replace("🔍", "[SEARCH]")
                    .replace("⭐", "[STAR]")
                    .replace("🎉", "[SUCCESS]")
                    .replace("💥", "[CRASH]")
                    .replace("🛑", "[STOP]")
                    .replace("⏸️", "[PAUSE]")
                    .replace("▶️", "[PLAY]")
                    .replace("🔁", "[REPEAT]")
                    .replace("📁", "[FOLDER]")
                    .replace("📄", "[FILE]")
                    .replace("🐍", "[PYTHON]")
                    .replace("🌟", "[NEW]")
                    .replace("🎪", "[EVENT]")
                    .replace("🏗️", "[BUILD]")
                    .replace("🔒", "[SECURE]")
                    .replace("🆘", "[HELP]")
                    .replace("👋", "[BYE]")
                    .replace("💻", "[COMPUTER]")
                    .replace("📡", "[NETWORK]")
                    .replace("🔎", "[FIND]")
                    .replace("📝", "[NOTES]")
                    .replace("🎭", "[MASK]")
                    .replace("🔥", "[HOT]")
                    .replace("⚡", "[FAST]")
                    .replace("🚨", "[URGENT]")
                    .replace("📸", "[CAPTURE]")
                    .replace("🏁", "[FINISH]")
                    .replace("🎰", "[RANDOM]")
                    .replace("🔐", "[LOCK]")
                    .replace("🔓", "[UNLOCK]")
                    .replace("📅", "[DATE]")
                    .replace("🕐", "[CLOCK]")
                    .replace("📮", "[MAIL]")
                    .replace("🧹", "[CLEAN]")
                    .replace("🔨", "[HAMMER]")
                    .replace("⏭️", "[SKIP]")
                    .replace("⏩", "[FAST_FORWARD]")
                    .replace("🏃", "[RUN]")
                    .replace("📱", "[MOBILE]")
                    .replace("💾", "[SAVE]")
                    .replace("🗃️", "[DATABASE]")
                    .replace("📊", "[CHART]")
                    .replace("📈", "[TRENDING]")
                    .replace("📉", "[DECLINING]")
                    .replace("🎲", "[DICE]")
                    .replace("🔮", "[CRYSTAL]")
                    .replace("🎨", "[ART]")
                    .replace("🛠️", "[TOOLS]")
                    .replace("⚙️", "[SETTINGS]")
                    .replace("🔧", "[WRENCH]")
                    .replace("🧰", "[TOOLBOX]")
                    .replace("📐", "[RULER]")
                    .replace("📏", "[MEASURE]")
                    .replace("🔬", "[MICROSCOPE]")
                    .replace("🔭", "[TELESCOPE]")
                    .replace("📖", "[BOOK]")
                    .replace("📚", "[BOOKS]")
                    .replace("📘", "[BLUE_BOOK]")
                    .replace("📙", "[ORANGE_BOOK]")
                    .replace("📗", "[GREEN_BOOK]")
                    .replace("📕", "[RED_BOOK]")
                    .replace("📒", "[LEDGER]")
                    .replace("📓", "[NOTEBOOK]")
                    .replace("📔", "[JOURNAL]")
                    .replace("📑", "[BOOKMARK]")
                    .replace("🔖", "[TAG]")
                    .replace("🏷️", "[LABEL]")
                    .replace("💼", "[BRIEFCASE]")
                    .replace("🗂️", "[DIVIDERS]")
                    .replace("📂", "[OPEN_FOLDER]")
                    .replace("📁", "[CLOSED_FOLDER]")
                    .replace("🗞️", "[NEWSPAPER]")
                    .replace("📰", "[NEWS]")
                )
                safe_args.append(safe_arg)
            else:
                safe_args.append(arg)
        
        print(*safe_args, **kwargs)

def get_emoji(unicode_char, fallback):
    """
    Get emoji if Unicode is supported, otherwise return fallback
    """
    try:
        # Test if we can encode the Unicode character
        unicode_char.encode(sys.stdout.encoding or 'utf-8')
        return unicode_char
    except (UnicodeEncodeError, AttributeError):
        return fallback

def setup_unicode_support():
    """
    Setup Unicode support for Windows
    """
    if platform.system() == "Windows":
        try:
            # Try to enable UTF-8 mode on Windows
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8')
            if hasattr(sys.stderr, 'reconfigure'):
                sys.stderr.reconfigure(encoding='utf-8')
        except:
            pass
        
        try:
            # Enable VT100 mode on Windows 10+
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except:
            pass

# Common emoji mappings for easy use
EMOJIS = {
    'success': get_emoji('✅', '[OK]'),
    'error': get_emoji('❌', '[ERROR]'),
    'warning': get_emoji('⚠️', '[WARNING]'),
    'rocket': get_emoji('🚀', '[START]'),
    'news': get_emoji('📰', '[NEWS]'),
    'cycle': get_emoji('🔄', '[CYCLE]'),
    'data': get_emoji('📊', '[DATA]'),
    'ai': get_emoji('🤖', '[AI]'),
    'time': get_emoji('⏰', '[TIME]'),
    'alert': get_emoji('🔔', '[ALERT]'),
    'web': get_emoji('🌐', '[WEB]'),
    'backup': get_emoji('📦', '[BACKUP]'),
    'setup': get_emoji('🔧', '[SETUP]'),
    'info': get_emoji('💡', '[INFO]'),
    'target': get_emoji('🎯', '[TARGET]'),
    'security': get_emoji('🛡️', '[SECURITY]'),
    'stop': get_emoji('🛑', '[STOP]'),
    'fast': get_emoji('⚡', '[FAST]'),
    'search': get_emoji('🔍', '[SEARCH]'),
}

# Initialize Unicode support when module is imported
setup_unicode_support()
