# -*- coding: utf-8 -*-
""" pyXBMCscraper implements the scraper framework version 1.1 of XBMC
http://wiki.xbmc.org/?title=Scrapers
http://wiki.xbmc.org/index.php?title=HOW-TO_Write_Media_Info_Scrapers
http://forum.xbmc.org/showthread.php?t=50055  ScraperXML Thread
http://forum.xbmc.org/showthread.php?t=98759

TODO:
multiple buffers ($$1$$2)
$INFO[language]
<url></url> spoof post
"""

__version__ = '0.1-dev'
__scraper_framework__ = 1.1


import os, re
import logging
#import urllib2
from exceptions import ValueError

import scraper

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)



def getScraper(path = None):
    """
    returns the correct subclass instance of class Scraper for a given path
    """
    path = os.path.normpath(path)
    addonxml = ElementTree()
    addonxml.parse( os.path.join(path, "addon.xml") )
    addonxml.find()
    
    