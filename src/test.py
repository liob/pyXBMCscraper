# -*- coding: utf-8 -*-
from se.scraper import xbmcMovieScraper
import pprint

pp = pprint.PrettyPrinter(indent=4)

movieScraper = xbmcMovieScraper("./scraper/metadata.themoviedb.org")
pp.pprint( movieScraper.search("Gladiator") )
#for movie in movieScraper.search("Gladiator"):
#    print "%s  -  %s" % (movie.title, movie.year)
#    print "   URL: %s" % movie.url
