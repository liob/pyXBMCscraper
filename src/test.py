import pyXBMCscraper

movieScraper = pyXBMCscraper.MovieScraper("metadata.themoviedb.org", "german")
movieScraper.search("Gladiator")
