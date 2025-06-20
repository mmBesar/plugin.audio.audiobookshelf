import sys
import urllib.parse as urlparse
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import requests
import json
import re

class AudiobookshelfPlugin:
    def __init__(self):
        self.addon = xbmcaddon.Addon()
        self.handle = int(sys.argv[1])
        self.server_url = self.addon.getSetting('server_url').rstrip('/')
        self.username = self.addon.getSetting('username')
        self.password = self.addon.getSetting('password')
        self.token = self.addon.getSetting('api_token') or None
        
    def login(self):
        # Use API token if available
        if self.token:
            return True
            
        if not all([self.server_url, self.username, self.password]):
            xbmcgui.Dialog().notification('Error', 'Please configure server settings', xbmcgui.NOTIFICATION_ERROR)
            return False
            
        try:
            resp = requests.post(f'{self.server_url}/login', 
                json={'username': self.username, 'password': self.password}, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                self.token = data.get('user', {}).get('token')
                if self.token:
                    # Save token for future use
                    self.addon.setSetting('api_token', self.token)
                    return True
        except Exception as e:
            xbmc.log(f'Login error: {str(e)}', xbmc.LOGERROR)
        
        xbmcgui.Dialog().notification('Error', 'Login failed', xbmcgui.NOTIFICATION_ERROR)
        return False
    
    def api_get(self, endpoint):
        if not self.token and not self.login():
            return None
        try:
            headers = {'Authorization': f'Bearer {self.token}'}
            resp = requests.get(f'{self.server_url}/api{endpoint}', headers=headers, timeout=15)
            return resp.json() if resp.status_code == 200 else None
        except Exception as e:
            xbmc.log(f'API error: {str(e)}', xbmc.LOGERROR)
            return None
    
    def get_cover_url(self, item_id):
        """Get cover URL with authentication token"""
        cover_url = f'{self.server_url}/api/items/{item_id}/cover'
        if self.token:
            cover_url += f'?token={self.token}'
        return cover_url
    
    def clean_html(self, text):
        """Remove HTML tags and decode HTML entities"""
        if not text:
            return ''
        
        # Remove image tags and their content completely
        text = re.sub(r'<img[^>]*>', '', text, flags=re.IGNORECASE)
        
        # Remove other problematic tags that might contain unwanted content
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.IGNORECASE | re.DOTALL)
        
        # Convert common HTML formatting to plain text equivalents
        text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<p[^>]*>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</p>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<div[^>]*>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</div>', '\n', text, flags=re.IGNORECASE)
        
        # Remove all remaining HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Decode HTML entities (more comprehensive list)
        html_entities = {
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&apos;': "'",
            '&nbsp;': ' ',
            '&#39;': "'",
            '&mdash;': '—',
            '&ndash;': '–',
            '&hellip;': '...',
            '&ldquo;': '"',
            '&rdquo;': '"',
            '&lsquo;': "'",
            '&rsquo;': "'",
            '&bull;': '•',
            '&copy;': '©',
            '&reg;': '®',
            '&trade;': '™'
        }
        
        for entity, char in html_entities.items():
            text = text.replace(entity, char)
        
        # Handle numeric HTML entities (like &#8217;)
        text = re.sub(r'&#(\d+);', lambda m: chr(int(m.group(1))) if int(m.group(1)) < 65536 else '', text)
        
        # Clean up extra whitespace and newlines
        text = re.sub(r'\n\s*\n', '\n\n', text)  # Multiple newlines to double newline
        text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces/tabs to single space
        text = text.strip()
        
        return text
    
    def format_duration(self, seconds):
        """Format duration in seconds to human readable format"""
        if not seconds:
            return ''
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        
        if hours > 0:
            return f'{hours}h {minutes}m'
        else:
            return f'{minutes}m'
    
    def get_episode_count(self, item_data):
        """Get accurate episode count from item data"""
        media = item_data.get('media', {})
        
        # Try different episode locations
        episodes = []
        if 'episodes' in media:
            episodes = media['episodes']
        elif 'episodes' in item_data:
            episodes = item_data['episodes']
        elif 'podcastEpisodes' in item_data:
            episodes = item_data['podcastEpisodes']
        
        return len(episodes) if episodes else 0
    
    def list_libraries(self):
        data = self.api_get('/libraries')
        if not data:
            return
            
        for lib in data.get('libraries', []):
            if lib.get('mediaType') in ['book', 'podcast']:
                media_type = lib.get('mediaType')
                name = f"{lib['name']} ({media_type.title()})"
                li = xbmcgui.ListItem(name)
                li.setInfo('music', {'title': name})
                url = f'{sys.argv[0]}?action=library&id={lib["id"]}&type={media_type}'
                xbmcplugin.addDirectoryItem(self.handle, url, li, True)
        
        xbmcplugin.endOfDirectory(self.handle)
    
    def play_item(self, item_id, media_type='book', episode_id=None):
        if media_type == 'podcast' and episode_id:
            # Get episode details first
            item_data = self.api_get(f'/items/{item_id}')
            if not item_data:
                xbmcgui.Dialog().notification('Error', 'Could not load podcast data', xbmcgui.NOTIFICATION_ERROR)
                return
            
            # Find the episode
            episodes = []
            media = item_data.get('media', {})
            
            if 'episodes' in media:
                episodes = media['episodes']
            elif 'episodes' in item_data:
                episodes = item_data['episodes']
            elif 'podcastEpisodes' in item_data:
                episodes = item_data['podcastEpisodes']
            
            episode = next((ep for ep in episodes if ep.get('id') == episode_id), None)
            if not episode:
                xbmcgui.Dialog().notification('Error', 'Episode not found', xbmcgui.NOTIFICATION_ERROR)
                return
            
            # Get the audio file from the episode
            audio_file = episode.get('audioFile')
            if not audio_file:
                xbmcgui.Dialog().notification('Error', 'No audio file found for episode', xbmcgui.NOTIFICATION_ERROR)
                return
            
            # Construct the stream URL using the file's ino (inode)
            file_ino = audio_file.get('ino')
            if not file_ino:
                xbmcgui.Dialog().notification('Error', 'Invalid audio file', xbmcgui.NOTIFICATION_ERROR)
                return
            
            stream_url = f'{self.server_url}/api/items/{item_id}/file/{file_ino}'
            if self.token:
                stream_url += f'?token={self.token}'
            
            # Get podcast metadata for episode
            podcast_metadata = media.get('metadata', {})
            podcast_title = podcast_metadata.get('title', 'Unknown Podcast')
            
            # Create ListItem with episode metadata
            title = episode.get('title', episode.get('episodeTitle', 'Episode'))
            description = self.clean_html(episode.get('description', episode.get('subtitle', '')))
            
            li = xbmcgui.ListItem(title)
            li.setInfo('music', {
                'title': title,
                'artist': podcast_title,
                'album': podcast_title,
                'plot': description,  # Use plot instead of comment
                'duration': int(episode.get('duration', audio_file.get('duration', 0)) or 0),
                'mediatype': 'song'
            })
            
            # Set artwork - use podcast cover
            cover_url = self.get_cover_url(item_id)
            li.setArt({
                'thumb': cover_url,
                'icon': cover_url,
                'fanart': cover_url
            })
            
            # Set the resolved URL
            li.setPath(stream_url)
            xbmcplugin.setResolvedUrl(self.handle, True, li)
            return
        
        # Handle audiobook playback
        item_data = self.api_get(f'/items/{item_id}')
        if not item_data:
            return
            
        media = item_data.get('media', {})
        audio_files = media.get('audioFiles', [])
        
        if not audio_files:
            xbmcgui.Dialog().notification('Error', 'No audio files found', xbmcgui.NOTIFICATION_ERROR)
            return
        
        # For single file audiobooks, resolve directly
        if len(audio_files) == 1:
            file_url = f'{self.server_url}/api/items/{item_id}/file/{audio_files[0]["ino"]}'
            if self.token:
                file_url += f'?token={self.token}'
            
            metadata = media.get('metadata', {})
            title = metadata.get('title', 'Unknown')
            author = metadata.get('authorName', 'Unknown Author')
            description = self.clean_html(metadata.get('description', ''))
            
            li = xbmcgui.ListItem(title)
            li.setInfo('music', {
                'title': title,
                'artist': author,
                'plot': description,  # Use plot instead of comment
                'duration': int(audio_files[0].get('duration', 0)),
                'mediatype': 'song'
            })
            
            # Set artwork
            cover_url = self.get_cover_url(item_id)
            li.setArt({
                'thumb': cover_url,
                'icon': cover_url,
                'fanart': cover_url
            })
            
            li.setPath(file_url)
            xbmcplugin.setResolvedUrl(self.handle, True, li)
            return
        
        # For multi-part audiobooks, create playlist
        playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
        playlist.clear()
        
        metadata = media.get('metadata', {})
        title = metadata.get('title', 'Unknown')
        author = metadata.get('authorName', 'Unknown Author')
        description = self.clean_html(metadata.get('description', ''))
        cover_url = self.get_cover_url(item_id)
        
        for i, audio_file in enumerate(audio_files):
            file_url = f'{self.server_url}/api/items/{item_id}/file/{audio_file["ino"]}'
            if self.token:
                file_url += f'?token={self.token}'
            
            li = xbmcgui.ListItem(f'{title} - Part {i+1}')
            li.setInfo('music', {
                'title': f'{title} - Part {i+1}',
                'artist': author,
                'album': title,
                'plot': description,  # Use plot instead of comment
                'duration': int(audio_file.get('duration', 0)),
                'tracknumber': i+1
            })
            
            # Set artwork for each part
            li.setArt({
                'thumb': cover_url,
                'icon': cover_url,
                'fanart': cover_url
            })
            
            li.setPath(file_url)
            playlist.add(file_url, li)
        
        xbmc.Player().play(playlist)
    
    def list_library_items(self, lib_id, media_type='book'):
        data = self.api_get(f'/libraries/{lib_id}/items?limit=100&include=rssfeed')
        if not data:
            return
            
        for item in data.get('results', []):
            media = item.get('media', {})
            metadata = media.get('metadata', {})
            
            if media_type == 'podcast':
                # For podcasts, get detailed item data to get accurate episode count
                detailed_item = self.api_get(f'/items/{item["id"]}')
                if not detailed_item:
                    continue
                
                title = metadata.get('title', 'Unknown Podcast')
                description = self.clean_html(metadata.get('description', ''))
                author = metadata.get('author', metadata.get('authorName', ''))
                
                # Get accurate episode count
                episode_count = self.get_episode_count(detailed_item)
                display_title = f'{title} ({episode_count} episodes)' if episode_count > 0 else title
                
                # Get additional podcast info
                genres = metadata.get('genres', [])
                genre_str = ', '.join(genres) if genres else ''
                
                li = xbmcgui.ListItem(display_title)
                li.setInfo('music', {
                    'title': title,
                    'artist': author,
                    'plot': description,  # Use plot instead of comment
                    'genre': genre_str,
                    'mediatype': 'album'
                })
                
                # Set artwork with authentication
                cover_url = self.get_cover_url(item['id'])
                li.setArt({
                    'thumb': cover_url,
                    'icon': cover_url,
                    'fanart': cover_url,
                    'poster': cover_url
                })
                
                url = f'{sys.argv[0]}?action=episodes&id={item["id"]}'
                xbmcplugin.addDirectoryItem(self.handle, url, li, True)
            else:
                # For books
                title = metadata.get('title', 'Unknown')
                author = metadata.get('authorName', 'Unknown Author')
                narrator = metadata.get('narratorName', '')
                description = self.clean_html(metadata.get('description', ''))
                duration = media.get('duration', 0)
                
                # Create display title with narrator if available
                display_author = f'{author}'
                if narrator and narrator != author:
                    display_author += f' (Narrated by {narrator})'
                
                duration_str = self.format_duration(duration)
                display_title = f'{title} - {display_author}'
                if duration_str:
                    display_title += f' [{duration_str}]'
                
                li = xbmcgui.ListItem(display_title)
                li.setInfo('music', {
                    'title': title,
                    'artist': author,
                    'plot': description,  # Use plot instead of comment
                    'duration': int(duration),
                    'mediatype': 'song'
                })
                li.setProperty('IsPlayable', 'true')
                
                # Set artwork with authentication
                cover_url = self.get_cover_url(item['id'])
                li.setArt({
                    'thumb': cover_url,
                    'icon': cover_url,
                    'fanart': cover_url,
                    'poster': cover_url
                })
                
                url = f'{sys.argv[0]}?action=play&id={item["id"]}&type=book'
                xbmcplugin.addDirectoryItem(self.handle, url, li, False)
        
        xbmcplugin.endOfDirectory(self.handle)
    
    def list_episodes(self, item_id):
        data = self.api_get(f'/items/{item_id}')
        if not data:
            return
            
        # Get podcast metadata
        media = data.get('media', {})
        podcast_metadata = media.get('metadata', {})
        podcast_title = podcast_metadata.get('title', 'Unknown Podcast')
        
        # Try different possible episode locations
        episodes = []
        
        if 'episodes' in media:
            episodes = media['episodes']
        elif 'episodes' in data:
            episodes = data['episodes']
        elif 'podcastEpisodes' in data:
            episodes = data['podcastEpisodes']
        
        if not episodes:
            li = xbmcgui.ListItem('No episodes found')
            xbmcplugin.addDirectoryItem(self.handle, '', li, False)
            xbmcplugin.endOfDirectory(self.handle)
            return
            
        # Get podcast cover URL for all episodes
        podcast_cover_url = self.get_cover_url(item_id)
        
        for ep in sorted(episodes, key=lambda x: x.get('publishedAt', 0), reverse=True):
            title = ep.get('title', ep.get('episodeTitle', 'Unknown Episode'))
            description = self.clean_html(ep.get('description', ep.get('subtitle', '')))
            
            # Handle publishedAt as timestamp or string
            pub_date = ''
            pub_year = ''
            if ep.get('publishedAt'):
                pub_timestamp = ep.get('publishedAt')
                if isinstance(pub_timestamp, int):
                    import datetime
                    dt = datetime.datetime.fromtimestamp(pub_timestamp / 1000)
                    pub_date = dt.strftime('%Y-%m-%d')
                    pub_year = dt.strftime('%Y')
                elif isinstance(pub_timestamp, str):
                    pub_date = pub_timestamp[:10]
                    pub_year = pub_timestamp[:4]
            
            duration = ep.get('duration', ep.get('audioFile', {}).get('duration', 0))
            duration_str = self.format_duration(duration) if duration else ''
            
            # Enhanced display title with duration
            display_title = title
            if pub_date:
                display_title = f'{title} ({pub_date})'
            if duration_str:
                display_title += f' [{duration_str}]'
            
            li = xbmcgui.ListItem(display_title)
            li.setInfo('music', {
                'title': title,
                'artist': podcast_title,
                'album': podcast_title,
                'plot': description,  # Use plot instead of comment
                'date': pub_date,
                'year': int(pub_year) if pub_year.isdigit() else 0,
                'duration': int(duration) if duration else 0,
                'mediatype': 'song'
            })
            li.setProperty('IsPlayable', 'true')
            
            # Use podcast artwork for episodes
            li.setArt({
                'thumb': podcast_cover_url,
                'icon': podcast_cover_url,
                'fanart': podcast_cover_url
            })
            
            ep_id = ep.get('id', ep.get('episodeId', ''))
            url = f'{sys.argv[0]}?action=play&id={item_id}&episode={ep_id}&type=podcast'
            xbmcplugin.addDirectoryItem(self.handle, url, li, False)
        
        xbmcplugin.endOfDirectory(self.handle)
    
    def router(self, params):
        if not params:
            self.list_libraries()
        elif params['action'] == 'library':
            media_type = params.get('type', 'book')
            self.list_library_items(params['id'], media_type)
        elif params['action'] == 'episodes':
            self.list_episodes(params['id'])
        elif params['action'] == 'play':
            media_type = params.get('type', 'book')
            episode_id = params.get('episode')
            self.play_item(params['id'], media_type, episode_id)

def run():
    params = dict(urlparse.parse_qsl(sys.argv[2][1:]))
    plugin = AudiobookshelfPlugin()
    plugin.router(params)

if __name__ == '__main__':
    run()
