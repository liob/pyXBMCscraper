from .scraper import scraper
from ...engine.xbmc import getScraper, mergeEtree

from xml.etree.ElementTree import ElementTree, tostring
from xml.etree.ElementTree import fromstring as ElementTree_fromstring
import os
import logging

class xbmcScraper(scraper):
    """
    the xbmcScraper class provides a generic ground foundation, which is
    required for all XBMC scrapers.
    """
    
    xml = ElementTree()          # holds the scraper regex xml tree
    addonxml = ElementTree()     # xml tree of addon.xml
    settingsxml= ElementTree()   # xml tree of resources/settings.xml
    path = None                  # filesystem path to scraper
    basepath = None              # the path which contains the scraper
    requires = []                # an array of dicts with the keys: scrpaer, version
    deps = []                    # contains the dependencies of the scraper as Scraper object
    
    def __init__(self, scraperPath = None):
        self.xml = ElementTree()
        self.addonxml = ElementTree()
        self.settingsxml= ElementTree()
        self.requires = []
        self.deps = []
        if scraperPath:
            scraperPath = os.path.normpath(scraperPath)
            self.addonxml.parse( os.path.join(scraperPath, "addon.xml") )
            xmlpath = self.addonxml.find("extension").attrib["library"]
            self.xml.parse( os.path.join(scraperPath, xmlpath) )
            if os.path.exists(os.path.join(scraperPath, "resources/settings.xml")):
                self.settingsxml.parse( os.path.join(scraperPath, "resources/settings.xml") )
            requires = self.addonxml.find("requires")
            if requires:
                for require in requires.findall("import"):
                    self.requires.append({})
                    self.requires[-1]["scraper"] = require.attrib["addon"]
                    self.requires[-1]["version"] = require.attrib["version"]
            else:
                logging.warning("could not find <requires> in %s/addon.xml" % scraperPath)
            self.basepath = os.path.split(scraperPath)[0]
        self.path = scraperPath
        if hasattr(self, "__stage2__"):
            self.__stage2__()
        
    def __stage2__(self):
        """ a customizable appendix to __init__ """
        
    def __resolve_deps__(self):
        """ resolve import dependencies of the scraper """
        for require in self.requires:
            if not require["scraper"] in ["xbmc.metadata",]:    # some deps are for xbmc only and are not scraper relevant
                logging.info("importing scraper %s as dependency." % require["scraper"])
                scraper = getScraper(os.path.join(self.basepath, require["scraper"]))
                scraper.__resolve_deps__()
                self.xml._setroot( mergeEtree( self.xml.getroot(), scraper.xml.getroot() ) )
    
    def search(self, name):
        """ dummy """
    
    