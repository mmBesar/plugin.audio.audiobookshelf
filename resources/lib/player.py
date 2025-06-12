#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import xbmc
import time
import threading

class AudiobookshelfPlayer(xbmc.Player):
    def __init__(self, episode_id, api):
        super(AudiobookshelfPlayer, self).__init__()
        self.episode_id = episode_id
        self.api = api
        self.is_playing = False
        self.total_time = 0
        self.current_time = 0
        self.last_sync_time = 0
        self.sync_interval = 30  # Sync every 30 seconds
        self.monitor = xbmc.Monitor()
        
        # Start monitoring thread
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_playback)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        xbmc.log(f'Audiobookshelf: Player initialized for episode {episode_id}', xbmc.LOGDEBUG)
    
    def onPlayBackStarted(self):
        """Called when playback starts"""
        xbmc.log('Audiobookshelf: Playback started', xbmc.LOGDEBUG)
        self.is_playing = True
        
        # Wait a bit for player to initialize
        time.sleep(1)
        
        try:
            self.total_time = self.getTotalTime()
            self.current_time = self.getTime()
            xbmc.log(f'Audiobookshelf: Total time: {self.total_time}, Current time: {self.current_time}', xbmc.LOGDEBUG)
        except:
            pass
    
    def onPlayBackPaused(self):
        """Called when playback is paused"""
        xbmc.log('Audiobookshelf: Playback paused', xbmc.LOGDEBUG)
        self.is_playing = False
        self._sync_progress()
    
    def onPlayBackResumed(self):
        """Called when playback resumes"""
        xbmc.log('Audiobookshelf: Playback resumed', xbmc.LOGDEBUG)
        self.is_playing = True
    
    def onPlayBackStopped(self):
        """Called when playback stops"""
        xbmc.log('Audiobookshelf: Playback stopped', xbmc.LOGDEBUG)
        self.is_playing = False
        self.monitoring = False
        self._sync_progress()
    
    def onPlayBackEnded(self):
        """Called when playback ends naturally"""
        xbmc.log('Audiobookshelf: Playback ended', xbmc.LOGDEBUG)
        self.is_playing = False
        self.monitoring = False
        
        # Mark episode as finished
        try:
            if self.total_time > 0:
                self.api.update_episode_progress(
                    self.episode_id, 
                    self.total_time, 
                    self.total_time, 
                    is_finished=True
                )
                xbmc.log('Audiobookshelf: Episode marked as finished', xbmc.LOGDEBUG)
        except Exception as e:
            xbmc.log(f'Audiobookshelf: Error marking episode as finished: {str(e)}', xbmc.LOGERROR)
    
    def onPlayBackSeek(self, time, seekOffset):
        """Called when user seeks"""
        xbmc.log(f'Audiobookshelf: Seek to {time}', xbmc.LOGDEBUG)
        self.current_time = time
        # Sync immediately after seek
        self._sync_progress()
    
    def _monitor_playback(self):
        """Monitor playback progress and sync periodically"""
        while self.monitoring and not self.monitor.abortRequested():
            if self.is_playing and self.isPlaying():
                try:
                    self.current_time = self.getTime()
                    if self.total_time == 0:
                        self.total_time = self.getTotalTime()
                    
                    # Sync progress every sync_interval seconds
                    current_timestamp = time.time()
                    if current_timestamp - self.last_sync_time >= self.sync_interval:
                        self._sync_progress()
                        self.last_sync_time = current_timestamp
                        
                except Exception as e:
                    xbmc.log(f'Audiobookshelf: Error in playback monitoring: {str(e)}', xbmc.LOGERROR)
            
            # Wait 5 seconds before next check
            if self.monitor.waitForAbort(5):
                break
        
        xbmc.log('Audiobookshelf: Playback monitoring stopped', xbmc.LOGDEBUG)
    
    def _sync_progress(self):
        """Sync current progress to server"""
        try:
            if self.current_time > 0 and self.total_time > 0:
                # Don't mark as finished unless we're really at the end
                is_finished = (self.total_time - self.current_time) < 30  # Within 30 seconds of end
                
                success = self.api.update_episode_progress(
                    self.episode_id,
                    self.current_time,
                    self.total_time,
                    is_finished=is_finished
                )
                
                if success:
                    xbmc.log(f'Audiobookshelf: Progress synced - {self.current_time}/{self.total_time}', xbmc.LOGDEBUG)
                else:
                    xbmc.log('Audiobookshelf: Failed to sync progress', xbmc.LOGWARNING)
                    
        except Exception as e:
            xbmc.log(f'Audiobookshelf: Error syncing progress: {str(e)}', xbmc.LOGERROR)
