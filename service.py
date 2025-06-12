#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import xbmc
import xbmcaddon
import time

class AudiobookshelfService:
    def __init__(self):
        self.addon = xbmcaddon.Addon()
        self.monitor = xbmc.Monitor()
        
        xbmc.log('Audiobookshelf: Service started', xbmc.LOGINFO)
    
    def run(self):
        """Main service loop"""
        while not self.monitor.abortRequested():
            # Check for setting changes
            if self.monitor.waitForAbort(60):  # Check every minute
                break
        
        xbmc.log('Audiobookshelf: Service stopped', xbmc.LOGINFO)

if __name__ == '__main__':
    service = AudiobookshelfService()
    service.run()
