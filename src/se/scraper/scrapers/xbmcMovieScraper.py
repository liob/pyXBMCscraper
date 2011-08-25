from .xbmcScraper import xbmcScraper

class xbmcMovieScraper(xbmcScraper):
    
    def __stage2__(self):
        self.__resolve_deps__()
    
    def __CreateSearchUrl__(self, querystring):
        """ generates a url for the given querystring """
        CreateSearchUrl = self.xml.find("CreateSearchUrl")
        dest = int( CreateSearchUrl.attrib["dest"] )
        # buffer[1] is used to input the querystring
        buffer = eval_regex( CreateSearchUrl.find("RegExp"), buffer={1:querystring,} )
        logging.info("searchurl: %s" % buffer[dest])
        return URL.fromstring(buffer[dest])
    
    def __DownloadSearchPage__(self, url):
        logging.info("downloading search page: %s" % url)
        return url.open().read()
    
    def __GetSearchResults__(self, page):
        """ parses the returned page """
        GetSearchResults = self.xml.find("GetSearchResults")
        dest = int( GetSearchResults.attrib["dest"] )
        buffer = eval_regex( GetSearchResults.find("RegExp"), buffer={1:page,} )
        return buffer[dest]
    
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
            rv.append(MovieSearchResult())
            for tag in ["title", "id", "year", "url"]:
                subelement = result.find(tag)
                if subelement is not None:
                    setattr(rv[-1], tag, subelement.text)
            for url in result.findall("url"):
                rv[-1].urls.append(URL.fromstring(url.text))
        return rv