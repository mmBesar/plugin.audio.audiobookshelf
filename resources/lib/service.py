#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Audiobookshelf Background Service
Handles progress synchronization and background tasks
"""

import time
import threading
from typing import Optional, Dict, Any
import json

import xbmc
import xbmcaddon
import xbmcgui

try:
    import requests
except ImportError:
    requests = None


class AudiobookshelfService:
    """Background service for Audiobookshelf addon"""
    
    def __init__(self):
        self.addon = xbmcaddon.Addon()
        self.addon_name = self.addon.getAddonInfo('name')
        self.monitor = xbmc.Monitor()
        self.player = xbmc.Player()
        
        # Service settings
        self.sync_interval = int(self.addon.getSetting('sync_interval') or '30')
        self.mark_finished_threshold = int(self.addon.getSetting('mark_finished_threshold') or '30')
        
        # State tracking
        self.current_item = None
        self.last_position = 0
        self.last_sync_time = 0
        self.is_audiobookshelf_content = False
        
        # Service control
        self._stop_event = threading.Event()
        
    def log(self, message: str, level: int = xbmc.LOGDEBUG) -> None:
        """Log message with service prefix"""
        xbmc.log(f"[{self.addon_name} Service] {message}", level)
        
    def get_server_config(self) -> tuple:
        """Get server URL and API token from settings"""
        server_url = self.addon.getSetting('server_url').rstrip('/')
        api_token = self.addon.getSetting('api_token')
        return server_url, api_token
        
    def make_request(self, endpoint: str, method: str = 'POST', data: Optional[Dict] = None) -> bool:
        """Make API request to sync progress"""
        server_url, api_token = self.get_server_config()
        
        if not server_url or not api_token:
            return False
            
        url = f"{server_url}/api/{endpoint}"
        headers = {'Authorization': f'Bearer {api_token}'}
        
        try:
            if requests:
                if method == 'POST':
                    response = requests.post(url, headers=headers, json=data, timeout=5)
                else:
                    response = requests.request(method, url, headers=headers, json=data, timeout=5)
                    
                response.raise_for_status()
                return True
            else:
                # Fallback implementation would go here
                self.log("Requests module not available for progress sync", xbmc.LOGWARNING)
                return False
                
        except Exception as e:
            self.log(f"Failed to sync progress: {str(e)}", xbmc.LOGWARNING)
            return False
    
    def extract_item_info(self, file_path: str) -> Optional[Dict[str, str]]:
        """Extract podcast and episode ID from file path/URL"""
        try:
            if 'audiobookshelf' in file_path and '/api/items/' in file_path:
                # Extract from URL like: /api/items/{podcast_id}/play/{episode_id}
                parts = file_path.split('/api/items/')[1].split('/')
                if len(parts) >= 3 and parts[1] == 'play':
                    return {
                        'podcast_id': parts[0],
                        'episode_id': parts[2].split('?')[0]  # Remove query parameters
                    }
        except Exception as e:
            self.log(f"Failed to extract item info: {str(e)}", xbmc.LOGDEBUG)
            
        return None
    
    def sync_progress(self, podcast_id: str, episode_id: str, current_time: float, 
                     duration: float, is_finished: bool = False) -> None:
        """Sync playback progress to Audiobookshelf server"""
        progress_data = {
            'currentTime': current_time,
            'duration': duration,
            'progress': min(current_time / duration, 1.0) if duration > 0 else 0,
            'isFinished': is_finished
        }
        
        endpoint = f"me/progress/{podcast_id}/{episode_id}"
        success = self.make_request(endpoint, 'POST', progress_data)
        
        if success:
            self.log(f"Synced progress: {current_time:.1f}s / {duration:.1f}s", xbmc.LOGDEBUG)
        else:
            self.log("Progress sync failed", xbmc.LOGWARNING)
    
    def on_playback_started(self) -> None:
        """Handle playback started event"""
        if not self.player.isPlaying():
            return
            
        try:
            file_path = self.player.getPlayingFile()
            self.current_item = self.extract_item_info(file_path)
            self.is_audiobookshelf_content = self.current_item is not None
            
            if self.is_audiobookshelf_content:
                self.log(f"Started playing Audiobookshelf content: {self.current_item}", xbmc.LOGDEBUG)
                self.last_position = 0
                self.last_sync_time = time.time()
                
        except Exception as e:
            self.log(f"Error in playback started handler: {str(e)}", xbmc.LOGWARNING)
    
    def on_playback_stopped(self) -> None:
        """Handle playback stopped event"""
        if self.is_audiobookshelf_content and self.current_item:
            try:
                # Final progress sync
                duration = self.player.getTotalTime()
                current_time = self.last_position
                
                # Check if episode should be marked as finished
                remaining_time = duration - current_time
                is_finished = remaining_time <= self.mark_finished_threshold
                
                self.sync_progress(
                    self.current_item['podcast_id'],
                    self.current_item['episode_id'],
                    current_time,
                    duration,
                    is_finished
                )
                
                self.log("Final progress sync on playback stop", xbmc.LOGDEBUG)
                
            except Exception as e:
                self.log(f"Error in playback stopped handler: {str(e)}", xbmc.LOGWARNING)
            finally:
                self.current_item = None
                self.is_audiobookshelf_content = False
    
    def update_progress(self) -> None:
        """Update current playback progress"""
        if not self.is_audiobookshelf_content or not self.current_item:
            return
            
        try:
            if self.player.isPlaying():
                current_time = self.player.getTime()
                self.last_position = current_time
                
                # Sync progress at regular intervals
                now = time.time()
                if now - self.last_sync_time >= self.sync_interval:
                    duration = self.player.getTotalTime()
                    if duration > 0:
                        self.sync_progress(
                            self.current_item['podcast_id'],
                            self.current_item['episode_id'],
                            current_time,
                            duration
                        )
                        self.last_sync_time = now
                        
        except Exception as e:
            self.log(f"Error updating progress: {str(e)}", xbmc.LOGDEBUG)
    
    def run(self) -> None:
        """Main service loop"""
        self.log("Audiobookshelf service started", xbmc.LOGINFO)
        
        # Player event monitoring
        class PlayerMonitor(xbmc.Player):
            def __init__(self, service):
                super().__init__()
                self.service = service
                
            def onPlayBackStarted(self):
                self.service.on_playback_started()
                
            def onPlayBackStopped(self):
                self.service.on_playback_stopped()
                
            def onPlayBackEnded(self):
                self.service.on_playback_stopped()
        
        player_monitor = PlayerMonitor(self)
        
        try:
            while not self.monitor.abortRequested() and not self._stop_event.is_set():
                # Update progress for currently playing content
                self.update_progress()
                
                # Sleep for 1 second intervals
                if self.monitor.waitForAbort(1):
                    break
                    
        except Exception as e:
            self.log(f"Service error: {str(e)}", xbmc.LOGERROR)
        finally:
            self.log("Audiobookshelf service stopped", xbmc.LOGINFO)
    
    def stop(self) -> None:
        """Stop the service"""
        self._stop_event.set()


# Global service instance for module-level access
_service_instance = None

def get_service() -> AudiobookshelfService:
    """Get the global service instance"""
    global _service_instance
    if _service_instance is None:
        _service_instance = AudiobookshelfService()
    return _service_instance
