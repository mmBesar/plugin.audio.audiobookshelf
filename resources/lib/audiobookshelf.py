#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import xbmc
import xbmcaddon
import xbmcgui
import json
from urllib.parse import urljoin, quote

class AudiobookshelfAPI:
    def __init__(self):
        self.addon = xbmcaddon.Addon()
        self.server_url = self.addon.getSettingString('server_url').rstrip('/')
        self.api_token = self.addon.getSettingString('api_token')
        self.session = requests.Session()
        
        if not self.server_url or not self.api_token:
            self.show_setup_dialog()
            return
        
        # Set up session with authentication
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        })
        
        # Test connection
        if not self.test_connection():
            xbmcgui.Dialog().notification('Audiobookshelf', 'Connection failed. Check settings.', xbmcgui.NOTIFICATION_ERROR)
    
    def show_setup_dialog(self):
        """Show setup dialog if server URL or API token is missing"""
        dialog = xbmcgui.Dialog()
        
        if not self.server_url:
            dialog.ok('Audiobookshelf Setup', 'Please configure your Audiobookshelf server URL in the add-on settings.')
        elif not self.api_token:
            dialog.ok('Audiobookshelf Setup', 'Please configure your API token in the add-on settings.')
        
        self.addon.openSettings()
    
    def test_connection(self):
        """Test connection to Audiobookshelf server"""
        try:
            response = self.session.get(f'{self.server_url}/api/ping', timeout=10)
            return response.status_code == 200
        except Exception as e:
            xbmc.log(f'Audiobookshelf: Connection test failed: {str(e)}', xbmc.LOGERROR)
            return False
    
    def get_libraries(self):
        """Get all libraries"""
        try:
            response = self.session.get(f'{self.server_url}/api/libraries')
            response.raise_for_status()
            return response.json()['libraries']
        except Exception as e:
            xbmc.log(f'Audiobookshelf: Error getting libraries: {str(e)}', xbmc.LOGERROR)
            return []
    
    def get_podcast_libraries(self):
        """Get podcast libraries only"""
        libraries = self.get_libraries()
        return [lib for lib in libraries if lib.get('mediaType') == 'podcast']
    
    def get_podcasts(self):
        """Get all podcasts from all podcast libraries"""
        podcasts = []
        podcast_libraries = self.get_podcast_libraries()
        
        for library in podcast_libraries:
            try:
                response = self.session.get(f'{self.server_url}/api/libraries/{library["id"]}/items')
                response.raise_for_status()
                data = response.json()
                podcasts.extend(data.get('results', []))
            except Exception as e:
                xbmc.log(f'Audiobookshelf: Error getting podcasts from library {library["id"]}: {str(e)}', xbmc.LOGERROR)
        
        return podcasts
    
    def get_podcast_info(self, podcast_id):
        """Get detailed podcast information"""
        try:
            response = self.session.get(f'{self.server_url}/api/items/{podcast_id}')
            response.raise_for_status()
            return response.json()
        except Exception as e:
            xbmc.log(f'Audiobookshelf: Error getting podcast info: {str(e)}', xbmc.LOGERROR)
            return None
    
    def get_podcast_episodes(self, podcast_id):
        """Get episodes for a specific podcast"""
        try:
            response = self.session.get(f'{self.server_url}/api/items/{podcast_id}')
            response.raise_for_status()
            data = response.json()
            
            # Episodes are in media.episodes
            episodes = data.get('media', {}).get('episodes', [])
            
            # Sort by publication date (newest first)
            episodes.sort(key=lambda x: x.get('publishedAt', ''), reverse=True)
            
            return episodes
        except Exception as e:
            xbmc.log(f'Audiobookshelf: Error getting podcast episodes: {str(e)}', xbmc.LOGERROR)
            return []
    
    def get_recent_episodes(self, limit=50):
        """Get recent episodes across all podcasts"""
        try:
            # Get all podcast libraries
            podcast_libraries = self.get_podcast_libraries()
            all_episodes = []
            
            for library in podcast_libraries:
                response = self.session.get(f'{self.server_url}/api/libraries/{library["id"]}/items')
                response.raise_for_status()
                data = response.json()
                
                # Get episodes from each podcast
                for podcast in data.get('results', []):
                    podcast_episodes = self.get_podcast_episodes(podcast['id'])
                    for episode in podcast_episodes:
                        episode['podcast'] = {
                            'id': podcast['id'],
                            'title': podcast['media']['metadata']['title']
                        }
                        all_episodes.append(episode)
            
            # Sort by publication date (newest first)
            all_episodes.sort(key=lambda x: x.get('publishedAt', ''), reverse=True)
            
            return all_episodes[:limit]
        except Exception as e:
            xbmc.log(f'Audiobookshelf: Error getting recent episodes: {str(e)}', xbmc.LOGERROR)
            return []
    
    def get_in_progress_episodes(self):
        """Get episodes that are currently in progress"""
        try:
            response = self.session.get(f'{self.server_url}/api/me/items-in-progress')
            response.raise_for_status()
            data = response.json()
            
            # Filter for podcast episodes only
            podcast_items = []
            for item in data.get('libraryItems', []):
                if item.get('mediaType') == 'podcast':
                    # Get the specific episode that's in progress
                    progress_info = item.get('userMediaProgress', {})
                    episode_id = progress_info.get('episodeId')
                    
                    if episode_id:
                        # Find the episode in the podcast
                        episodes = item.get('media', {}).get('episodes', [])
                        for episode in episodes:
                            if episode['id'] == episode_id:
                                podcast_items.append({
                                    'episode': episode,
                                    'progress': progress_info,
                                    'podcast_id': item['id'],
                                    'podcast_title': item['media']['metadata']['title']
                                })
                                break
            
            return podcast_items
        except Exception as e:
            xbmc.log(f'Audiobookshelf: Error getting in progress episodes: {str(e)}', xbmc.LOGERROR)
            return []
    
    def get_episode_info(self, episode_id):
        """Get detailed episode information"""
        try:
            # Episode info is usually retrieved as part of podcast info
            # This is a placeholder - you might need to adjust based on your needs
            return None
        except Exception as e:
            xbmc.log(f'Audiobookshelf: Error getting episode info: {str(e)}', xbmc.LOGERROR)
            return None
    
    def get_episode_stream_url(self, episode_id):
        """Get streaming URL for an episode"""
        try:
            # The stream URL format for Audiobookshelf
            stream_url = f'{self.server_url}/api/items/{episode_id}/play'
            
            # Add authentication token as query parameter
            stream_url += f'?token={self.api_token}'
            
            return stream_url
        except Exception as e:
            xbmc.log(f'Audiobookshelf: Error getting stream URL: {str(e)}', xbmc.LOGERROR)
            return None
    
    def get_episode_progress(self, episode_id):
        """Get playback progress for an episode"""
        try:
            response = self.session.get(f'{self.server_url}/api/me/progress/{episode_id}')
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception as e:
            xbmc.log(f'Audiobookshelf: Error getting episode progress: {str(e)}', xbmc.LOGERROR)
            return None
    
    def update_episode_progress(self, episode_id, current_time, duration, is_finished=False):
        """Update playback progress for an episode"""
        try:
            data = {
                'currentTime': current_time,
                'duration': duration,
                'isFinished': is_finished
            }
            
            response = self.session.patch(f'{self.server_url}/api/me/progress/{episode_id}', json=data)
            response.raise_for_status()
            return True
        except Exception as e:
            xbmc.log(f'Audiobookshelf: Error updating episode progress: {str(e)}', xbmc.LOGERROR)
            return False
    
    def get_cover_url(self, item_id):
        """Get cover image URL for an item"""
        return f'{self.server_url}/api/items/{item_id}/cover?token={self.api_token}'
    
    def mark_episode_finished(self, episode_id):
        """Mark an episode as finished"""
        try:
            response = self.session.patch(f'{self.server_url}/api/me/progress/{episode_id}/finish')
            response.raise_for_status()
            return True
        except Exception as e:
            xbmc.log(f'Audiobookshelf: Error marking episode as finished: {str(e)}', xbmc.LOGERROR)
            return False
