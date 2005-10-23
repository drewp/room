
import socket, os, xmlrpclib, logging
import RDF

log = logging.getLogger("rdfaction")

class RoomAction:
    """perform actions described in the KB"""
    
    def __init__(self, filename="/my/proj/room/midicodes.n3"):
        self.filename = filename
        self.load_rdf()
        self.connect_light()

    def load_rdf(self):
        self.model = RDF.Model(RDF.MemoryStorage())
        u = RDF.Uri("file:%s" % self.filename)
        try:
            for s in RDF.Parser('turtle').parse_as_stream(u):
                self.model.add_statement(s)
        except (Exception, ), e:
            # e.__class__.__module__ is "RDF", not the real module!
            if e.__class__.__name__ != "RedlandError":
                raise
            raise ValueError("Error parsing %s: %s" % (u, e))
        
    def connect_light(self):
        self.light_server = xmlrpclib.ServerProxy("http://dot:%s" %
                                     socket.getservbyname("lights","tcp"))

    def fire(self, pred, obj):
        """

        fire actions with given pred/obj (both must be quoted n3)
        
        """
        self.load_rdf()
        
        model = self.model
        prefixes = """PREFIX midi: <http://projects.bigasterisk.com/midi/>
                      PREFIX room: <http://projects.bigasterisk.com/room/>
                      """

        matches = 0
        for res in RDF.SPARQLQuery(prefixes + '''
                SELECT ?action
                WHERE {
                    [%s %s; room:triggers ?action] .
                }''' % (pred,obj)).execute(model):
            action = res['action'].uri
            matches = matches + 1
            log.info("running action %s" % action)

            for res in RDF.SPARQLQuery(prefixes + '''
                    SELECT ?light ?level
                    WHERE {
                     <%s> room:lightLevel [room:light ?light; room:to ?level] .
                    }''' % action).execute(model):
                self.do_lightlevel(res['light'].uri, res['level'])

            for res in RDF.SPARQLQuery(prefixes + '''
                    SELECT ?command
                    WHERE {
                        <%s> room:execute ?command.
                    }''' % action).execute(model):
                log.info("running %s" % str(res['command']))
                ret = os.system(str(res['command']))
                if ret != 0:
                    log.error("command returned %d" % (ret >> 8))

        if matches == 0:
            log.debug("no commands matched %r %r" % (pred,obj))
        return matches
                    
    def do_lightlevel(self, light_uri, level):
        prefix = "http://projects.bigasterisk.com/room/lights/"
        lightname = str(light_uri)[len(prefix):]

        assert (level.literal_value['datatype'] ==
                RDF.Uri("http://www.w3.org/2001/XMLSchema#float"))
        level = float(level.literal_value['string'])

        self.set_light(lightname, level)
            
    def set_light(self, name, lev):
        try:
            log.info("%s to %s" % (name,lev))
            self.light_server.setLight(name,lev)
        except xmlrpclib.Fault, e:
            log.error("%s on command setLight(%r,%r)" % (e, name, lev))
            self.connect_light()
