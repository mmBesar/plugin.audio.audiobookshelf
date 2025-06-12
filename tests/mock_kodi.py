# mock_kodi.py - Mock Kodi modules for testing
"""
Mock Kodi modules to allow import testing outside of Kodi environment.
Place this file in tests/ directory.
"""
import sys
from unittest.mock import MagicMock

# Mock all Kodi modules
kodi_modules = [
    'xbmc',
    'xbmcgui', 
    'xbmcaddon',
    'xbmcplugin',
    'xbmcvfs'
]

for module in kodi_modules:
    sys.modules[module] = MagicMock()

# Mock common Kodi constants
sys.modules['xbmc'].LOGDEBUG = 0
sys.modules['xbmc'].LOGINFO = 1
sys.modules['xbmc'].LOGWARNING = 2
sys.modules['xbmc'].LOGERROR = 3

# Mock common Kodi functions
sys.modules['xbmc'].log = MagicMock()
sys.modules['xbmc'].translatePath = MagicMock(return_value='/mock/path')
sys.modules['xbmc'].getInfoLabel = MagicMock(return_value='mock_info')

# Mock addon functionality
sys.modules['xbmcaddon'].Addon = MagicMock()

# Mock GUI components
sys.modules['xbmcgui'].ListItem = MagicMock()
sys.modules['xbmcgui'].Dialog = MagicMock()

# Mock plugin functionality
sys.modules['xbmcplugin'].addDirectoryItem = MagicMock()
sys.modules['xbmcplugin'].endOfDirectory = MagicMock()
sys.modules['xbmcplugin'].setResolvedUrl = MagicMock()

print("✓ Kodi modules mocked successfully")
