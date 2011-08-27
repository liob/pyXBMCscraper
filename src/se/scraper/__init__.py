import os

scrapersDir = os.path.join(__path__[0], "scrapers")

# load the scrapers located in ./scrapers in the global namespace of the modul
# to enable you to directly access the classes
for item in os.listdir(scrapersDir):
    if item.endswith(".py") and item != "__init__.py":
        # ok, it is a python file and not the init
        moduleName = item.rsplit(".", 1)[0]
        tmp = __import__('scrapers', globals(), locals(), [moduleName], -1)
        module = getattr(tmp, moduleName)
        globals()[moduleName] = getattr(module, moduleName)