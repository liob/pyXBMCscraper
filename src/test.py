# -*- coding: utf-8 -*-
import pyXBMCscraper

movieScraper = pyXBMCscraper.MovieScraper("metadata.themoviedb.org", "german")
for movie in movieScraper.search("Gladiator"):
    print "%s  -  %s" % (movie["title"], str(movie["year"]))
    print "   URL: %s" % movie["url"]
