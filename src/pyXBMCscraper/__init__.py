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
__scraper_framework__ = "1.1"


import os, re
import logging
import urllib2
from xml.etree.ElementTree import ElementTree as ElementTree
from xml.etree.ElementTree import fromstring as ElementTree_fromstring
from exceptions import ValueError

#movie_scraper = "metadata.themoviedb.org"
#tvshows_scraper = "metadata.tvdb.com"

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
scraper_dir = "scraper/"

class Movie(object):
    pass

class MovieScraper(object):
    
    xml = None
    language = None
    
    def __init__(self, scraper, language):
        self.xml = get_scraper_xml(scraper)
        self.language = language
    
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
            rv.append({})
            for tag in ["title", "id", "year", "url"]:
                subelement = result.find(tag)
                if subelement is not None:
                    rv[-1][tag] = subelement.text
                else:
                    rv[-1][tag] = None
        return rv

class URL(object):
    """
    URL handles xbmc <url> tags. It implements a generic interface with the following options:
        url:   specifiy the url
        spoof: the referrer url which should be send. This is sometimes needed for pages with direct linking protection.
        post:  if the post attribute is present variables in the url will be send via POST
    """
    
    spoof = None
    post  = None
    url   = None

    @classmethod
    def fromstring(cls, string):
        """
        create an URL instance from a given string.
        The string may be plain 'http://host/path' or valid xml '<url spoof="">http://host/path</url>'
        """
        logging.debug("initializing URL instance with following string: %s" % string)
        url = cls()
        string = string.strip()
        if string[0:4].lower() == "http":
            # this is a plain url string
            cls.__parseURL__(url, string)
        else:
            # we assume its valid xml
            urltree = ElementTree_fromstring(string)
            url.url = urltree.text
            url.spoof = urltree.find("spoof")
            url.post = urltree.find("post")
        return url
    
    def __parseURL__(self, string):
        self.url = string
    
    def open(self):
        """ returns a file handler """
        headers={
                 'User-Agent' : 'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.12) Gecko/20101027 Firefox/3.6.12',
                 'Connection' : 'close'
                 }
        if self.spoof:
            headers['Referer'] = self.spoof
            
        req = urllib2.Request(url=self.url,
                              data=self.post,
                              headers=headers)
        logging.debug("opening url: %s   headers: %s    spoof: %s    post: %s" % (self.url, str(headers), self.spoof, self.post) )
        return urllib2.urlopen(req)
    
def eval_regex(tree, buffer={}):
    """
    accepts RegExp Etree objects and evaluates them 
        repeat="yes" -> will repeat the expression as long as there are matches
        noclean="1" -> will NOT strip html tags and special characters from field 1. Field can be 1 ... 9. By default, all fields are "cleaned"
        trim="1" -> trim white spaces of field 1. Field can be 1 ... 9
        clear="yes" -> if there is no match for the expression, dest will be cleared. By default, dest will keep it previous value
    """
    
    def get_buffer_value(identifier):
        if identifier[0:1] == '\\':
            slot = int(identifier[1:])
            if slot in buffer:
                return buffer[slot]
            else:
                return ""
        if identifier[0:2] == '$$':
            slot = int(identifier[2:])
            if slot in buffer:
                return buffer[slot]
            else:
                return ""
        raise ValueError
    
    def string2boolean(string):
        """ converts a given string to True or False """
        if string.lower() in ["true", "1", "yes"]:
            return True
        elif string.lower() in ["false", "0", "no"]:
            return False
        else:
            logging.error("could not convert \"%s\" to boolean!" % string)
            raise ValueError
        
    def string2array(string):
        rv = []
        for sub in string.split(","):
            sub = sub.strip()
            rv.append(int(sub))
        return rv
    
    def stripHTML(string):
        """
        strip html tags from string and convert special chars
            '&' (Ampersand/kaufmännisches Und) wird zu '&amp;'.
            '"' (doppeltes Anführungszeichen) wird zu '&quot;', wenn ENT_NOQUOTES nicht gesetzt ist.
            ''' (einfaches Anführungszeichen) wird nur zu '&#039;', wenn ENT_QUOTES gesetzt ist.
            '<' (kleiner als) wird zu '&lt;'
            '>' (größer als) wird zu '&gt;'
        """
        conv = [ ['&amp;','&'], ['&quot;','"'], ['&#039;',"'"], ['&lt;','<'], ['&gt;','>'] ]
        # first we need to get rid of the html tags
        taglvl = 0
        rv = ""
        for char in string:
            if char == "<":
                taglvl += 1
            elif char == ">":
                taglvl -= 1
                if taglvl < 0:
                    logging.error("invalid html syntax: \n%s" % string)
                    raise ValueError
            else:
                if taglvl == 0:
                    rv += char
        # replace html special chars
        for convItem in conv:
            rv = rv.replace(convItem[0], convItem[1])
        return rv
    
    def expand(matchObj, template, noclean=[], trim=[]):
        """ expands the backrefs in template with matchobject """
        numbers = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
        escape = False
        result = ""
        
        for char in template:
            if escape:
                # a \ preceded the current char
                if char in numbers:
                    # ok, we have a backreference like "\1"
                    if int(char) > matchObj.lastindex:
                        logging.error("cannot resolve backreference %s in %s" % (char, template) )
                        raise ValueError
                    escape = False
                    ref = matchObj.group( int(char) )
                    if not int(char) in noclean:
                        ref = stripHTML(ref)
                    if int(char) in trim:
                        ref = ref.strip()
                    result += ref
                #elif char == "\\":
                #    # we have an escaped backspace. this transforms in a normal backspace
                #    escape = False
                #    result += "\\"
                else:
                    # the preceding \ appears to be a normal char
                    escape = False
                    result += "\\" + char
                    
            else:
                if char == "\\":
                    # char is a backspace. This could be a backref
                    escape = True
                else:
                    # it is a normal char as in [a-z,A-Z,0-9...]
                    result += char 
        return result
    

    input = tree.attrib["input"]
    dest = tree.attrib["dest"]
    if dest[-1:] == "+":
        dest = int(dest[0:-1])
        dest_append = True
    else:
        dest = int(dest)
        dest_append = False
    output = tree.attrib["output"]
    exprObj = tree.find("expression")
    expr = exprObj.text
    if expr == None:
        # if expr is not set it should match everything
        expr = "(.*)"
    if "repeat" in exprObj.attrib:
        repeat = string2boolean(exprObj.attrib["repeat"])
    else:
        repeat = False
    if "clear" in exprObj.attrib:
        clear = string2boolean(exprObj.attrib["clear"])
    else:
        clear = False
    if "noclean" in exprObj.attrib:
        noclean = string2array(exprObj.attrib["noclean"])
    else:
        noclean = []
    if "trim" in exprObj.attrib:
        trim = string2array(exprObj.attrib["trim"])
    else:
        trim = []
    
    for regex in tree.findall("RegExp"):
        buffer = eval_regex(regex, buffer)
    
    logging.debug("evaluating with expr: \"%s\" \noutput: %s \nData: %s" % (expr, output, get_buffer_value(input)))
    eval = ""
    cregex = re.compile(expr, re.MULTILINE|re.DOTALL)
    if repeat:
        for matchObj in cregex.finditer( get_buffer_value(input) ):
            #eval += matchObj.expand(output)
            eval += expand(matchObj, output, noclean, trim)
            clear = False
    else:
        matchObj = cregex.search( get_buffer_value(input) )
        if matchObj:
            #eval = matchObj.expand(output)
            eval = expand(matchObj, output, noclean, trim)
            clear = False
    
    if eval:
        logging.debug("dest: %i append: %s Result: %s" % (dest, str(dest_append), eval) )
        if dest_append:
            buffer[dest] += eval
        else:
            buffer[dest] = eval
    
    if clear:
        buffer[dest] = ""
        
    return buffer

    

def get_scraper_xml(scraper):
    my_scraper_dir = os.path.join(scraper_dir, scraper)
    addon_xml = ElementTree()
    addon_xml.parse("%s/addon.xml" % my_scraper_dir)
    libname = addon_xml.find("extension").attrib["library"]
    scraper_xml = ElementTree()
    scraper_xml.parse("%s/%s" % (my_scraper_dir, libname))
    return scraper_xml

