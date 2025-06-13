"""
Mock Kodi modules for testing outside of Kodi environment.
This module provides mock implementations of all Kodi-specific modules.
"""

import sys
from unittest.mock import Mock, MagicMock


class MockXbmc:
    """Mock xbmc module"""
    LOGDEBUG = 0
    LOGINFO = 1
    LOGWARNING = 2
    LOGERROR = 3
    LOGFATAL = 4
    
    PLAYLIST_MUSIC = 0
    PLAYLIST_VIDEO = 1
    
    # Player constants
    PLAYER_CORE_AUTO = 0
    PLAYER_CORE_DVDPLAYER = 1
    PLAYER_CORE_MPLAYER = 2
    PLAYER_CORE_PAPLAYER = 3
    
    @staticmethod
    def log(msg, level=LOGDEBUG):
        """Mock log function"""
        levels = {0: 'DEBUG', 1: 'INFO', 2: 'WARNING', 3: 'ERROR', 4: 'FATAL'}
        print(f"[KODI {levels.get(level, 'DEBUG')}] {msg}")
    
    @staticmethod
    def translatePath(path):
        """Mock translatePath function"""
        return path.replace('special://', '/tmp/kodi/')
    
    @staticmethod
    def executebuiltin(builtin):
        """Mock executebuiltin function"""
        print(f"[KODI BUILTIN] {builtin}")
    
    @staticmethod
    def getCondVisibility(condition):
        """Mock getCondVisibility function"""
        return False
    
    @staticmethod
    def getInfoLabel(infotag):
        """Mock getInfoLabel function"""
        return ""
    
    @staticmethod
    def sleep(time):
        """Mock sleep function"""
        import time as t
        t.sleep(time / 1000.0)  # Kodi sleep is in milliseconds
    
    @staticmethod
    def Monitor():
        """Mock Monitor class"""
        return MockMonitor()
    
    @staticmethod
    def Player():
        """Mock Player class"""
        return MockPlayer()
    
    @staticmethod
    def PlayList(playlist_type):
        """Mock PlayList class"""
        return MockPlayList()


class MockMonitor:
    """Mock xbmc.Monitor class"""
    def __init__(self):
        self._aborted = False
    
    def abortRequested(self):
        return self._aborted
    
    def waitForAbort(self, timeout=None):
        if timeout:
            import time
            time.sleep(timeout)
        return self._aborted


class MockPlayer:
    """Mock xbmc.Player class"""
    def __init__(self):
        self._playing = False
        self._time = 0
        self._total_time = 0
    
    def play(self, item=None, listitem=None, windowed=False, startpos=-1):
        self._playing = True
    
    def stop(self):
        self._playing = False
    
    def pause(self):
        pass
    
    def isPlaying(self):
        return self._playing
    
    def getTime(self):
        return self._time
    
    def getTotalTime(self):
        return self._total_time
    
    def seekTime(self, time):
        self._time = time


class MockPlayList:
    """Mock xbmc.PlayList class"""
    def __init__(self):
        self._items = []
    
    def add(self, url, listitem=None, index=-1):
        if index == -1:
            self._items.append((url, listitem))
        else:
            self._items.insert(index, (url, listitem))
    
    def clear(self):
        self._items = []
    
    def size(self):
        return len(self._items)


class MockXbmcgui:
    """Mock xbmcgui module"""
    
    # Dialog constants
    ALPHANUM_HIDE_INPUT = 1
    PASSWORD_VERIFY = 2
    
    @staticmethod
    def ListItem(label="", label2="", path=""):
        """Mock ListItem class"""
        return MockListItem(label, label2, path)
    
    @staticmethod
    def Dialog():
        """Mock Dialog class"""
        return MockDialog()
    
    @staticmethod
    def getCurrentWindowId():
        """Mock getCurrentWindowId function"""
        return 10000


class MockListItem:
    """Mock xbmcgui.ListItem class"""
    def __init__(self, label="", label2="", path=""):
        self.label = label
        self.label2 = label2
        self.path = path
        self._info = {}
        self._art = {}
        self._properties = {}
    
    def setLabel(self, label):
        self.label = label
    
    def setLabel2(self, label):
        self.label2 = label
    
    def setPath(self, path):
        self.path = path
    
    def setInfo(self, type, infoLabels):
        self._info[type] = infoLabels
    
    def setArt(self, values):
        self._art.update(values)
    
    def setProperty(self, key, value):
        self._properties[key] = value
    
    def getProperty(self, key):
        return self._properties.get(key, "")


class MockDialog:
    """Mock xbmcgui.Dialog class"""
    
    def ok(self, heading, message):
        print(f"[DIALOG OK] {heading}: {message}")
        return True
    
    def yesno(self, heading, message, nolabel="", yeslabel=""):
        print(f"[DIALOG YESNO] {heading}: {message}")
        return True
    
    def notification(self, heading, message, icon="", time=5000, sound=True):
        print(f"[NOTIFICATION] {heading}: {message}")
    
    def textviewer(self, heading, text):
        print(f"[TEXT VIEWER] {heading}: {text[:100]}...")
    
    def input(self, heading, defaultt="", type=0, option=0, autoclose=0):
        print(f"[INPUT DIALOG] {heading}")
        return "mock_input"
    
    def numeric(self, type, heading, defaultt=""):
        print(f"[NUMERIC DIALOG] {heading}")
        return "123"
    
    def browse(self, type, heading, shares, mask="", useThumbs=False, treatAsFolder=False, defaultt=""):
        print(f"[BROWSE DIALOG] {heading}")
        return "/mock/path"


class MockXbmcplugin:
    """Mock xbmcplugin module"""
    
    # Sort methods
    SORT_METHOD_NONE = 0
    SORT_METHOD_LABEL = 1
    SORT_METHOD_TITLE = 2
    SORT_METHOD_DATE = 3
    SORT_METHOD_DURATION = 4
    
    # Content types
    CONTENT_NONE = ""
    CONTENT_ALBUMS = "albums"
    CONTENT_SONGS = "songs"
    CONTENT_ARTISTS = "artists"
    
    @staticmethod
    def addDirectoryItem(handle, url, listitem, isFolder=False, totalItems=0):
        """Mock addDirectoryItem function"""
        return True
    
    @staticmethod
    def endOfDirectory(handle, succeeded=True, updateListing=False, cacheToDisc=True):
        """Mock endOfDirectory function"""
        pass
    
    @staticmethod
    def setResolvedUrl(handle, succeeded, listitem):
        """Mock setResolvedUrl function"""
        pass
    
    @staticmethod
    def addSortMethod(handle, sortMethod):
        """Mock addSortMethod function"""
        pass
    
    @staticmethod
    def setContent(handle, content):
        """Mock setContent function"""
        pass
    
    @staticmethod
    def setPluginCategory(handle, category):
        """Mock setPluginCategory function"""
        pass
    
    @staticmethod
    def setPluginFanart(handle, image, color1=None, color2=None, color3=None):
        """Mock setPluginFanart function"""
        pass


class MockXbmcaddon:
    """Mock xbmcaddon module"""
    
    @staticmethod
    def Addon(id=None):
        """Mock Addon class"""
        return MockAddon(id)


class MockAddon:
    """Mock xbmcaddon.Addon class"""
    def __init__(self, id=None):
        self.id = id or "mock.addon"
        self._settings = {}
    
    def getSetting(self, id):
        return self._settings.get(id, "")
    
    def setSetting(self, id, value):
        self._settings[id] = value
    
    def getSettingBool(self, id):
        return self._settings.get(id, False)
    
    def getSettingInt(self, id):
        return int(self._settings.get(id, 0))
    
    def getSettingNumber(self, id):
        return float(self._settings.get(id, 0.0))
    
    def getAddonInfo(self, id):
        info = {
            'id': self.id,
            'name': 'Mock Addon',
            'version': '1.0.0',
            'path': '/mock/addon/path',
            'profile': '/mock/profile/path',
            'fanart': '/mock/fanart.jpg',
            'icon': '/mock/icon.png'
        }
        return info.get(id, "")
    
    def getLocalizedString(self, id):
        return f"Localized String {id}"
    
    def openSettings(self):
        pass


class MockXbmcvfs:
    """Mock xbmcvfs module"""
    
    @staticmethod
    def exists(path):
        """Mock exists function"""
        return True
    
    @staticmethod
    def mkdir(path):
        """Mock mkdir function"""
        return True
    
    @staticmethod
    def mkdirs(path):
        """Mock mkdirs function"""
        return True
    
    @staticmethod
    def rmdir(path):
        """Mock rmdir function"""
        return True
    
    @staticmethod
    def delete(file):
        """Mock delete function"""
        return True
    
    @staticmethod
    def copy(source, destination):
        """Mock copy function"""
        return True
    
    @staticmethod
    def rename(file, newFileName):
        """Mock rename function"""
        return True
    
    @staticmethod
    def listdir(path):
        """Mock listdir function"""
        return ([], [])  # (dirs, files)


# Install all mocks into sys.modules
def install_mocks():
    """Install all mock modules into sys.modules"""
    sys.modules['xbmc'] = MockXbmc()
    sys.modules['xbmcgui'] = MockXbmcgui()
    sys.modules['xbmcplugin'] = MockXbmcplugin()
    sys.modules['xbmcaddon'] = MockXbmcaddon()
    sys.modules['xbmcvfs'] = MockXbmcvfs()


# Automatically install mocks when this module is imported
install_mocks()
