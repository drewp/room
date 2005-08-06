
import logging

def commonlogsetup(excludechannels=[], filename="log"):
    """sets up logs how i usually like them, with a custom filter to
    exclude the given channel names. log level is DEBUG. return value
    is the top-level logger"""
    if isinstance(excludechannels,(str,unicode)):
        excludechannels=[excludechannels]
    class myfilter(logging.Filter):
        def filter(self,record,excludechannels=excludechannels):
            return record.name not in excludechannels
    log=logging.getLogger()
    log.setLevel(logging.DEBUG)

    handlers = [logging.StreamHandler()]
    if filename is not None:
        handlers.append(logging.FileHandler(filename))
    for h in handlers:
        h.setFormatter(logging.Formatter("%(created)s %(asctime)s %(levelname)-5s %(filename)s:%(lineno)d: %(message)s"))
        h.addFilter(myfilter())
        log.addHandler(h)
    return log
