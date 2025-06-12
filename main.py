#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
from urllib.parse import urlencode, parse_qsl
from resources.lib.audiobookshelf import AudiobookshelfAPI

# Get addon info
addon = xbmcaddon.Addon()
addon_handle = int(sys.argv[1])
addon_url = sys.argv[0]

def get_url(**kwargs):
    """Create plugin URL with parameters"""
    return '{}?{}'.format(addon_url, urlencode(kwargs))

def list_categories():
    """List main categories"""
    categories = [
        ('podcasts', 'Podcasts', 'DefaultMusicAlbums.png'),
        ('recent_episodes', 'Recent Episodes', 'DefaultMusicSongs.png'),
        ('in_progress', 'In Progress', 'DefaultMusicSongs.png'),
    ]
    
    for category_id, title, icon in categories:
        li = xbmcgui.ListItem(label=title)
        li.setArt({'thumb': icon, 'icon': icon})
        li.setInfo('music', {'title': title})
        
        url = get_url(action='category', category=category_id)
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
    
    xbmcplugin.endOfDirectory(addon_handle)

def list_podcasts():
    """List all podcasts"""
    try:
        api = AudiobookshelfAPI()
        podcasts = api.get_podcasts()
        
        if not podcasts:
            xbmcgui.Dialog().notification('Audiobookshelf', 'No podcasts found', xbmcgui.NOTIFICATION_INFO)
            xbmcplugin.endOfDirectory(addon_handle)
            return
        
        for podcast in podcasts:
            li = xbmcgui.ListItem(label=podcast['media']['metadata']['title'])
            
            # Set artwork
            if podcast['media']['coverPath']:
                cover_url = api.get_cover_url(podcast['id'])
                li.setArt({'thumb': cover_url, 'poster': cover_url})
            
            # Set info
            li.setInfo('music', {
                'title': podcast['media']['metadata']['title'],
                'artist': podcast['media']['metadata'].get('author', ''),
                'plot': podcast['media']['metadata'].get('description', ''),
                'mediatype': 'album'
            })
            
            url = get_url(action='episodes', podcast_id=podcast['id'])
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
        
        xbmcplugin.setContent(addon_handle, 'albums')
        xbmcplugin.endOfDirectory(addon_handle)
        
    except Exception as e:
        xbmc.log(f'Audiobookshelf: Error listing podcasts: {str(e)}', xbmc.LOGERROR)
        xbmcgui.Dialog().notification('Audiobookshelf', 'Error loading podcasts', xbmcgui.NOTIFICATION_ERROR)
        xbmcplugin.endOfDirectory(addon_handle)

def list_episodes(podcast_id):
    """List episodes for a podcast"""
    try:
        api = AudiobookshelfAPI()
        episodes = api.get_podcast_episodes(podcast_id)
        podcast_info = api.get_podcast_info(podcast_id)
        
        if not episodes:
            xbmcgui.Dialog().notification('Audiobookshelf', 'No episodes found', xbmcgui.NOTIFICATION_INFO)
            xbmcplugin.endOfDirectory(addon_handle)
            return
        
        for episode in episodes:
            title = episode.get('title', 'Unknown Episode')
            li = xbmcgui.ListItem(label=title)
            
            # Set artwork from podcast
            if podcast_info and podcast_info.get('media', {}).get('coverPath'):
                cover_url = api.get_cover_url(podcast_id)
                li.setArt({'thumb': cover_url, 'poster': cover_url})
            
            # Set info
            duration = episode.get('duration', 0)
            pub_date = episode.get('publishedAt', '')
            
            li.setInfo('music', {
                'title': title,
                'artist': podcast_info['media']['metadata'].get('author', '') if podcast_info else '',
                'album': podcast_info['media']['metadata'].get('title', '') if podcast_info else '',
                'plot': episode.get('description', ''),
                'duration': int(duration),
                'date': pub_date[:10] if pub_date else '',
                'mediatype': 'song'
            })
            
            # Set as playable
            li.setProperty('IsPlayable', 'true')
            
            # Get progress info
            progress = api.get_episode_progress(episode['id'])
            if progress and progress.get('currentTime', 0) > 0:
                # Mark as partially played
                li.setProperty('ResumeTime', str(progress['currentTime']))
                li.setProperty('TotalTime', str(duration))
            
            url = get_url(action='play', episode_id=episode['id'], podcast_id=podcast_id)
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=False)
        
        xbmcplugin.setContent(addon_handle, 'songs')
        xbmcplugin.endOfDirectory(addon_handle)
        
    except Exception as e:
        xbmc.log(f'Audiobookshelf: Error listing episodes: {str(e)}', xbmc.LOGERROR)
        xbmcgui.Dialog().notification('Audiobookshelf', 'Error loading episodes', xbmcgui.NOTIFICATION_ERROR)
        xbmcplugin.endOfDirectory(addon_handle)

def list_recent_episodes():
    """List recent episodes across all podcasts"""
    try:
        api = AudiobookshelfAPI()
        episodes = api.get_recent_episodes()
        
        if not episodes:
            xbmcgui.Dialog().notification('Audiobookshelf', 'No recent episodes found', xbmcgui.NOTIFICATION_INFO)
            xbmcplugin.endOfDirectory(addon_handle)
            return
        
        for episode in episodes:
            title = episode.get('title', 'Unknown Episode')
            podcast_title = episode.get('podcast', {}).get('title', 'Unknown Podcast')
            
            li = xbmcgui.ListItem(label=f'{title} - {podcast_title}')
            
            # Set info
            duration = episode.get('duration', 0)
            pub_date = episode.get('publishedAt', '')
            
            li.setInfo('music', {
                'title': title,
                'artist': podcast_title,
                'plot': episode.get('description', ''),
                'duration': int(duration),
                'date': pub_date[:10] if pub_date else '',
                'mediatype': 'song'
            })
            
            li.setProperty('IsPlayable', 'true')
            
            url = get_url(action='play', episode_id=episode['id'], podcast_id=episode.get('podcast', {}).get('id', ''))
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=False)
        
        xbmcplugin.setContent(addon_handle, 'songs')
        xbmcplugin.endOfDirectory(addon_handle)
        
    except Exception as e:
        xbmc.log(f'Audiobookshelf: Error listing recent episodes: {str(e)}', xbmc.LOGERROR)
        xbmcgui.Dialog().notification('Audiobookshelf', 'Error loading recent episodes', xbmcgui.NOTIFICATION_ERROR)
        xbmcplugin.endOfDirectory(addon_handle)

def list_in_progress():
    """List episodes that are currently in progress"""
    try:
        api = AudiobookshelfAPI()
        episodes = api.get_in_progress_episodes()
        
        if not episodes:
            xbmcgui.Dialog().notification('Audiobookshelf', 'No episodes in progress', xbmcgui.NOTIFICATION_INFO)
            xbmcplugin.endOfDirectory(addon_handle)
            return
        
        for item in episodes:
            episode = item.get('episode', {})
            progress = item.get('progress', {})
            
            title = episode.get('title', 'Unknown Episode')
            podcast_title = item.get('podcast_title', 'Unknown Podcast')
            
            li = xbmcgui.ListItem(label=f'{title} - {podcast_title}')
            
            # Set info
            duration = episode.get('duration', 0)
            current_time = progress.get('currentTime', 0)
            
            li.setInfo('music', {
                'title': title,
                'artist': podcast_title,
                'plot': episode.get('description', ''),
                'duration': int(duration),
                'mediatype': 'song'
            })
            
            li.setProperty('IsPlayable', 'true')
            li.setProperty('ResumeTime', str(current_time))
            li.setProperty('TotalTime', str(duration))
            
            url = get_url(action='play', episode_id=episode['id'], podcast_id=item.get('podcast_id', ''))
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=False)
        
        xbmcplugin.setContent(addon_handle, 'songs')
        xbmcplugin.endOfDirectory(addon_handle)
        
    except Exception as e:
        xbmc.log(f'Audiobookshelf: Error listing in progress: {str(e)}', xbmc.LOGERROR)
        xbmcgui.Dialog().notification('Audiobookshelf', 'Error loading in progress episodes', xbmcgui.NOTIFICATION_ERROR)
        xbmcplugin.endOfDirectory(addon_handle)

def play_episode(episode_id, podcast_id):
    """Play an episode"""
    try:
        api = AudiobookshelfAPI()
        stream_url = api.get_episode_stream_url(episode_id)
        
        if not stream_url:
            xbmcgui.Dialog().notification('Audiobookshelf', 'Could not get stream URL', xbmcgui.NOTIFICATION_ERROR)
            return
        
        # Create playitem
        li = xbmcgui.ListItem(path=stream_url)
        
        # Get episode info for better playback experience
        episode_info = api.get_episode_info(episode_id)
        if episode_info:
            li.setInfo('music', {
                'title': episode_info.get('title', ''),
                'duration': episode_info.get('duration', 0)
            })
        
        # Set resume point if available
        progress = api.get_episode_progress(episode_id)
        if progress and progress.get('currentTime', 0) > 0:
            li.setProperty('ResumeTime', str(progress['currentTime']))
        
        # Start playback
        xbmcplugin.setResolvedUrl(addon_handle, True, li)
        
        # Start progress monitoring
        from resources.lib.player import AudiobookshelfPlayer
        player = AudiobookshelfPlayer(episode_id, api)
        
    except Exception as e:
        xbmc.log(f'Audiobookshelf: Error playing episode: {str(e)}', xbmc.LOGERROR)
        xbmcgui.Dialog().notification('Audiobookshelf', 'Error playing episode', xbmcgui.NOTIFICATION_ERROR)
        xbmcplugin.setResolvedUrl(addon_handle, False, xbmcgui.ListItem())

def router(paramstring):
    """Route URL parameters to appropriate functions"""
    params = dict(parse_qsl(paramstring))
    
    if not params:
        list_categories()
    elif params['action'] == 'category':
        if params['category'] == 'podcasts':
            list_podcasts()
        elif params['category'] == 'recent_episodes':
            list_recent_episodes()
        elif params['category'] == 'in_progress':
            list_in_progress()
    elif params['action'] == 'episodes':
        list_episodes(params['podcast_id'])
    elif params['action'] == 'play':
        play_episode(params['episode_id'], params.get('podcast_id', ''))

if __name__ == '__main__':
    router(sys.argv[2][1:])  # Remove leading '?'
