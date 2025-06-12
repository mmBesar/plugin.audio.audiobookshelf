#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Audiobookshelf Service - Entry Point
Simplified service entry point for Kodi addon checker compliance
"""

from resources.lib.service import AudiobookshelfService

if __name__ == '__main__':
    service = AudiobookshelfService()
    service.run()
