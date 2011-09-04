from .xbmcScraper import xbmcScraper
from ...engine.xbmc import gvRegex, URL, xml2dict

import logging
from xml.etree.ElementTree import fromstring as ElementTree_fromstring

class xbmcMovieScraper(xbmcScraper):
    
    def __stage2__(self):
        self.__resolve_deps__()
    
    def __CreateSearchUrl__(self, querystring):
        """ generates a url for the given querystring """
        CreateSearchUrl = self.xml.find("CreateSearchUrl")
        if not CreateSearchUrl:
            raise ValueError("could not find CreateSearchUrl")
        # buffer[1] is used to input the querystring
        rv = gvRegex( CreateSearchUrl, self.xml.getroot(), buffer={1:querystring,} )
        logging.info("searchurl: %s" % rv)
        return URL.fromstring(rv)
    
    def __DownloadSearchPage__(self, url):
        return url.open().read()
    
    def __GetSearchResults__(self, page):
        """ parses the returned page """
        root = self.xml.getroot()
        return gvRegex( root.find("GetSearchResults"), root, buffer={1:page,} )
    
    def __GetDetails__(self, page):
        root = self.xml.getroot()
        return gvRegex( root.find("GetDetails"), root, buffer={1:page,} )
    
    def search(self, name):
        """ 
        returns an array where each entry is a hit in the results:
            [  {title: "Gladiator",
                id: "98",
                year: "2000",
                url: "http://api.themoviedb.org/2.1/Movie.getInfo/$INFO[language]/xml/57983e31fb435df4df77afb854740ea9/98"}
                {...},
                ...
        """
        url = self.__CreateSearchUrl__(name)
        page = self.__DownloadSearchPage__(url)
        results = self.__GetSearchResults__(page)
        results_xml = ElementTree_fromstring(results)
        rv = []
        for result in results_xml.findall("entity"):
            rv.append({})
            rv[-1]["urls"] = []
            for tag in ["title", "id", "year"]:
                subelement = result.find(tag)
                if subelement is not None:
                    rv[-1][tag] = subelement.text
            for url in result.findall("url"):
                rv[-1]["urls"].append(URL.fromstring(url.text))
        return rv
    
    def info(self, searchResult):
        info = self.__GetDetails__( searchResult["urls"][0].open().read() )
        info = ElementTree_fromstring(info)
        return xml2dict(info)