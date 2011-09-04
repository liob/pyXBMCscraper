import os
import logging
import re
import urllib2
from copy import deepcopy
from xml.etree.ElementTree import ElementTree
from xml.etree.ElementTree import fromstring as ElementTree_fromstring

def getScraper(path = None):
    """
    returns the correct subclass instance of class xbmcScraper for a given path
    """
    from ..scraper.scrapers import xbmcMovieScraper, xbmcScraperLibrary
    
    assoc = {"xbmc.metadata.scraper.library": xbmcScraperLibrary.xbmcScraperLibrary,
             "xbmc.metadata.scraper.movies": xbmcMovieScraper.xbmcMovieScraper,
             }
    path = os.path.normpath(path)
    addonxml = ElementTree()
    addonxml.parse( os.path.join(path, "addon.xml") )
    for match in addonxml.findall("extension"):
        if "library" in match.attrib:
            return assoc[ match.attrib["point"] ](path)
    raise
            

def xml2dict(node):
    """ convert a etree node to a python list """
    rv = {}
    if len(node) > 1:
        rv[node.tag] = []
        for subnode in node:
            found = False
            for item in rv[node.tag]:
                print item.keys()
                if subnode.tag in item.keys():
                    item[subnode.tag].append(xml2dict(subnode)[subnode.tag][0])
                    found = True
            if not found:
                rv[node.tag].append(xml2dict(subnode))
    else:
        value = node.text
        if value.strip() == "":
            value = None
        rv[node.tag] = [value,]
    return rv

def mergeEtree(tree1, tree2):
    """ take tree1 and tree2 and return a merged tree, where tree1 and tree2 are instances of ElementTree.Element """
    mtree = deepcopy(tree1)
    tree2 = deepcopy(tree2)
    
    for elementToMerge in tree2:
        found = False
        for element in mtree:
            if elementToMerge.tag == element.tag:
                found = True
        if not found:
            mtree.append(elementToMerge)
    return mtree
    

def gvRegex(subtree, tree, buffer={}):
    """ evauluate the regex subtree and return the value in the dest buffer """
    dest = int( subtree.attrib["dest"] )
    regExp = subtree[0]
    buffer = evalRegex(regExp, tree, buffer)
    return buffer[dest]
    

def evalRegex(subtree, tree, buffer={}):
    """
    evaluate a regex subtree. This is the workhorse of this library.
    the complete tree is required to evaluate custom functions.
        repeat="yes" -> will repeat the expression as long as there are matches
        noclean="1" -> will NOT strip html tags and special characters from field 1. Field can be 1 ... 9. By default, all fields are "cleaned"
        trim="1" -> trim white spaces of field 1. Field can be 1 ... 9
        clear="yes" -> if there is no match for the expression, dest will be cleared. By default, dest will keep it previous value
    """
    
    def get_buffer_value(identifier):
        """
        read a buffer value specified by its identifier.
        a identifier can be $$n or \n where n specifies the slot.
        also it is possible to join multiple buffers. i.e.: $$1$$2
        would return the values of slot 1+2.
        """
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
        logging.warn("could not find identifier %s in buffer. returning \"\"" % identifier)
        return ""
    
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
        """
        converts a string in the format "one,to,three" 
        to an array ["one","two","three"]
        """
        rv = []
        for sub in string.split(","):
            sub = sub.strip()
            rv.append(int(sub))
        return rv
    
    def stripHTML(string):
        """
        strip html tags from string and convert special chars
            '&' => '&amp;'
            '"' => '&quot;'
            ''' => '&#039;'
            '<' => '&lt;'
            '>' => '&gt;'
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
    
    def evalCustomFunct(string):
        """ evaluate and expand the custom functions """
        urlregex = re.compile(u"\<url[A-Z,a-z,0-9, ,\=,\=,\"]*?>.*?\<\/url\>", re.MULTILINE|re.DOTALL)
        while True:
            matchObj = urlregex.search(string)
            if not matchObj:
                # if no match was found break!
                break
            span = matchObj.span()
            url = URL.fromstring(matchObj.group())
            s = s[0:span[0]] + url.customFunction(tree) + s[span[1]:]
    

    input = subtree.attrib["input"]
    dest = subtree.attrib["dest"]
    if dest[-1:] == "+":
        dest = int(dest[0:-1])
        dest_append = True
    else:
        dest = int(dest)
        dest_append = False
    output = subtree.attrib["output"]
    exprObj = subtree.find("expression")
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
    
    for regex in subtree.findall("RegExp"):
        buffer = evalRegex(regex, tree, buffer)
    
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



class URL(object):
    """
    URL handles xbmc <url> tags. It implements a generic interface with the following options:
        url:   specifiy the url
        spoof: the referrer url which should be send. This is sometimes needed for pages with direct linking protection.
        post:  if the post attribute is present variables in the url will be send via POST
    """
    
    spoof    = None
    post     = None
    url      = None
    function = None

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
            if "function" in urltree.attrib:
                url.function = urltree.attrib["function"]
        return url
    
    def __parseURL__(self, string):
        self.url = string
    
    def open(self):
        """ returns a file handler """
        logging.info("downloading URL: %s //spoof: %s post: %s" % (self.url, str(self.spoof), str(self.post)))
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
    
    def customFunction(self, tree):
        """ evaluate the custom function of this url object """
        cfunct = tree[self.function]
        return gvRegex( cfunct, tree, buffer={1:self.open.read(),} )
        