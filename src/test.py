# -*- coding: utf-8 -*-
from se.scraper import xbmcMovieScraper
import pprint
import xml.etree.ElementTree

pp = pprint.PrettyPrinter(indent=4)

movieScraper = xbmcMovieScraper("./scraper/metadata.themoviedb.org")
results = movieScraper.search("Gladiator")
#pp.pprint(results)
pp.pprint(results[0])
pp.pprint( movieScraper.info(results[0]) )
#print movieScraper.info(results[0]).find("title").text