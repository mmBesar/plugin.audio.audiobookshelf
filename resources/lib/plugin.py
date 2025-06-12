#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Audiobookshelf Kodi Plugin - Main Logic
"""

import sys
import urllib.parse as urlparse
import urllib.request as urllib2
import json
import time
from typing import Dict, List, Optional, Any

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmcvfs

try:
    import requests
except ImportError:
    xbmc.log("Audiobookshelf: requests module not available, using urllib", xbmc.LOGWARNING)
    requests = None


class AudiobookshelfPlugin:
    """Main plugin class for Audiobookshelf Kodi addon"""
    
    def __init__(self):
        self.addon = xbmcaddon.Addon()
        self.addon_id = self.addon.getAddonInfo('id')
        self.addon_name = self.addon.getAddonInfo('name')
        self.addon_version = self.addon.getAddonInfo('version')
        self.addon_path = self.addon.getAddonInfo('path')
        
        # Plugin handle and URL
        self.handle = int(sys.argv[1]) if len(sys.argv) > 1 else -1
        self.base_url = sys.argv[0] if len(sys.argv) > 0 else ''
        
        # Parse plugin arguments
        if len(sys.argv) > 2:
            self.params = dict(urlparse.parse_qsl(sys.argv[2][1:]))
        else:
            self.params = {}
            
        # Settings
        self.server_url = self.addon.getSetting('server_url').rstrip('/')
        self.api_token = self.addon.getSetting('api_token')
        self.episodes_per_page = int(self.addon.getSetting('episodes_per_page') or '50')
        self.auto_resume = self.addon.getSettingBool('auto_resume')
        self.show_descriptions = self.addon.getSettingBool('show_descriptions')
        self.sort_newest_first = self.addon.getSettingBool('sort_newest_first')
        
        # Headers for API requests
        self.headers = {'Authorization': f'Bearer {self.api_token}'} if self.api_token else {}
        
    def log(self, message: str, level: int = xbmc.LOGDEBUG) -> None:
        """Log message with addon prefix"""
        xbmc.log(f"[{self.addon_name}] {message}", level)
        
    def make_request(self, endpoint: str, method: str = 'GET', data: Optional[Dict] = None) -> Optional[Dict]:
        """Make API request to Audiobookshelf server"""
        if not self.server_url or not self.api_token:
            self.log("Server URL or API token not configured", xbmc.LOGERROR)
            return None
            
        url = f"{self.server_url}/api/{endpoint}"
        
        try:
            if requests:
                if method == 'GET':
                    response = requests.get(url, headers=self.headers, timeout=10)
                elif method == 'POST':
                    response = requests.post(url, headers=self.headers, json=data, timeout=10)
                else:
                    response = requests.request(method, url, headers=self.headers, json=data, timeout=10)
                    
                response.raise_for_status()
                return response.json()
            else:
                # Fallback to urllib
                req = urllib2.Request(url)
                for key, value in list(self.headers.items()):
                    req.add_header(key, value)
                    
                if data and method in ['POST', 'PUT']:
                    req.data = json.dumps(data).encode('utf-8')
                    req.add_header('Content-Type', 'application/json')
                    
                response = urllib2.urlopen(req, timeout=10)
                return json.loads(response.read().decode('utf-8'))
                
        except Exception as e:
            self.log(f"API request failed: {str(e)}", xbmc.LOGERROR)
            return None
    
    def test_connection(self) -> bool:
        """Test connection to Audiobookshelf server"""
        result = self.make_request('ping')
        return result is not None
        
    def get_podcasts(self) -> Optional[List[Dict]]:
        """Get list of podcasts from server"""
        libraries = self.make_request('libraries')
        if not libraries:
            return None
            
        podcasts = []
        for library in libraries.get('libraries', []):
            if library.get('mediaType') == 'podcast':
                library_items = self.make_request(f"libraries/{library['id']}/items")
                if library_items:
                    podcasts.extend(library_items.get('results', []))
                    
        return podcasts
        
    def get_podcast_episodes(self, podcast_id: str) -> Optional[List[Dict]]:
        """Get episodes for a specific podcast"""
        podcast = self.make_request(f"items/{podcast_id}")
        if not podcast:
            return None
            
        episodes = podcast.get('media', {}).get('episodes', [])
        
        if self.sort_newest_first:
            episodes.sort(key=lambda x: x.get('publishedAt', ''), reverse=True)
        else:
            episodes.sort(key=lambda x: x.get('publishedAt', ''))
            
        return episodes
        
    def get_recent_episodes(self) -> Optional[List[Dict]]:
        """Get recent episodes across all podcasts"""
        podcasts = self.get_podcasts()
        if not podcasts:
            return None
            
        all_episodes = []
        for podcast in podcasts:
            episodes = self.get_podcast_episodes(podcast['id'])
            if episodes:
                for episode in episodes[:5]:  # Latest 5 from each podcast
                    episode['podcast_title'] = podcast.get('media', {}).get('metadata', {}).get('title', 'Unknown')
                    all_episodes.append(episode)
                    
        # Sort by publish date
        all_episodes.sort(key=lambda x: x.get('publishedAt', ''), reverse=True)
        return all_episodes[:self.episodes_per_page]
        
    def get_in_progress_episodes(self) -> Optional[List[Dict]]:
        """Get episodes that are currently in progress"""
        progress = self.make_request('me/progress')
        if not progress:
            return None
            
        in_progress = []
        for item in progress.get('libraryItems', []):
            if item.get('progress', 0) > 0 and item.get('progress', 0) < 1:
                episode_data = self.make_request(f"items/{item['libraryItemId']}")
                if episode_data:
                    in_progress.append(episode_data)
                    
        return in_progress
        
    def build_url(self, **kwargs) -> str:
        """Build plugin URL with parameters"""
        return f"{self.base_url}?{urlparse.urlencode(kwargs)}"
        
    def add_directory_item(self, title: str, url: str, is_folder: bool = True, 
                          info_labels: Optional[Dict] = None, art: Optional[Dict] = None,
                          context_menu: Optional[List] = None) -> None:
        """Add directory item to Kodi"""
        list_item = xbmcgui.ListItem(label=title)
        
        if info_labels:
            list_item.setInfo('music', info_labels)
            
        if art:
            list_item.setArt(art)
            
        if context_menu:
            list_item.addContextMenuItems(context_menu)
            
        xbmcplugin.addDirectoryItem(self.handle, url, list_item, is_folder)
        
    def show_main_menu(self) -> None:
        """Show main plugin menu"""
        self.add_directory_item(
            "Podcasts",
            self.build_url(action='list_podcasts'),
            True
        )
        
        self.add_directory_item(
            "Recent Episodes", 
            self.build_url(action='recent_episodes'),
            True
        )
        
        self.add_directory_item(
            "In Progress",
            self.build_url(action='in_progress'),
            True
        )
        
        self.add_directory_item(
            "Settings",
            self.build_url(action='settings'),
            False
        )
        
        xbmcplugin.endOfDirectory(self.handle)
        
    def show_podcasts(self) -> None:
        """Show list of podcasts"""
        podcasts = self.get_podcasts()
        if not podcasts:
            xbmcgui.Dialog().notification(self.addon_name, "Failed to load podcasts", xbmcgui.NOTIFICATION_ERROR)
            return
            
        for podcast in podcasts:
            metadata = podcast.get('media', {}).get('metadata', {})
            title = metadata.get('title', 'Unknown Podcast')
            description = metadata.get('description', '')
            
            info_labels = {
                'title': title,
                'plot': description if self.show_descriptions else '',
                'genre': 'Podcast'
            }
            
            art = {}
            if metadata.get('coverPath'):
                art['thumb'] = f"{self.server_url}{metadata['coverPath']}"
                
            self.add_directory_item(
                title,
                self.build_url(action='list_episodes', podcast_id=podcast['id']),
                True,
                info_labels,
                art
            )
            
        xbmcplugin.setContent(self.handle, 'albums')
        xbmcplugin.endOfDirectory(self.handle)
        
    def show_episodes(self, podcast_id: str) -> None:
        """Show episodes for a podcast"""
        episodes = self.get_podcast_episodes(podcast_id)
        if not episodes:
            xbmcgui.Dialog().notification(self.addon_name, "Failed to load episodes", xbmcgui.NOTIFICATION_ERROR)
            return
            
        for episode in episodes:
            title = episode.get('title', 'Unknown Episode')
            description = episode.get('description', '')
            duration = episode.get('audioFile', {}).get('duration', 0)
            
            info_labels = {
                'title': title,
                'plot': description if self.show_descriptions else '',
                'duration': int(duration),
                'mediatype': 'song'
            }
            
            # Get episode audio URL
            audio_url = f"{self.server_url}/api/items/{podcast_id}/play/{episode['id']}"
            if self.api_token:
                audio_url += f"?token={self.api_token}"
                
            self.add_directory_item(
                title,
                audio_url,
                False,
                info_labels
            )
            
        xbmcplugin.setContent(self.handle, 'songs')
        xbmcplugin.endOfDirectory(self.handle)
        
    def show_recent_episodes(self) -> None:
        """Show recent episodes"""
        episodes = self.get_recent_episodes()
        if not episodes:
            xbmcgui.Dialog().notification(self.addon_name, "No recent episodes found", xbmcgui.NOTIFICATION_INFO)
            return
            
        for episode in episodes:
            title = f"{episode.get('podcast_title', '')} - {episode.get('title', 'Unknown')}"
            description = episode.get('description', '')
            
            info_labels = {
                'title': title,
                'plot': description if self.show_descriptions else '',
                'mediatype': 'song'
            }
            
            # This would need the podcast ID to build the proper URL
            # For now, just add as folder item
            self.add_directory_item(title, "#", False, info_labels)
            
        xbmcplugin.setContent(self.handle, 'songs')
        xbmcplugin.endOfDirectory(self.handle)
        
    def show_settings(self) -> None:
        """Open addon settings"""
        self.addon.openSettings()
        
    def route(self) -> None:
        """Route requests based on action parameter"""
        action = self.params.get('action', 'main')
        
        if action == 'main':
            self.show_main_menu()
        elif action == 'list_podcasts':
            self.show_podcasts()
        elif action == 'list_episodes':
            podcast_id = self.params.get('podcast_id')
            if podcast_id:
                self.show_episodes(podcast_id)
        elif action == 'recent_episodes':
            self.show_recent_episodes()
        elif action == 'in_progress':
            self.show_recent_episodes()  # Placeholder
        elif action == 'settings':
            self.show_settings()
        else:
            self.show_main_menu()


def run_plugin() -> None:
    """Main plugin entry point"""
    try:
        plugin = AudiobookshelfPlugin()
        plugin.route()
    except Exception as e:
        xbmc.log(f"Audiobookshelf Plugin Error: {str(e)}", xbmc.LOGERROR)
        xbmcgui.Dialog().notification("Audiobookshelf", "Plugin error occurred", xbmcgui.NOTIFICATION_ERROR)
