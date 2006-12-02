
import socket, os, logging
import alsaaudio
import RDF

log = logging.getLogger("rdfaction")

class RoomAction:
    """perform actions described in the KB"""
    prefixes = """PREFIX midi: <http://projects.bigasterisk.com/midi/>
    PREFIX room: <http://projects.bigasterisk.com/room/>
    """
    
    def __init__(self, filename="/my/proj/room/midicodes.n3",
                 withTwisted=False):
        self.filename = filename
        self.model = None
        self.modelMtime = None
        self.load_rdf()
        self.withTwisted = withTwisted

    def load_rdf(self):
        mtime = os.path.getmtime(self.filename)
        if self.model is not None and mtime <= self.modelMtime:
            return
        self.modelMtime = mtime
            
        log.info("loading rdf from %r" % self.filename)
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

    def action_uris(self):
        return [node.uri for node in
                self.model.get_sources(
            # class should be type. fix midicodes.n3 too.
            RDF.Uri("http://www.w3.org/2000/01/rdf-schema#Class"),
            RDF.Uri("http://projects.bigasterisk.com/room/action"))]
        
    def fire(self, pred, obj):
        """
        fire actions with given pred/obj (both must be quoted n3)
        """
        try:
            self.load_rdf()
        except ValueError:
            log.debug("cannot search for actions")
            return
        
        model = self.model

        matches = 0
        for res in RDF.SPARQLQuery(self.prefixes + '''
                SELECT ?action
                WHERE {
                    [%s %s; room:triggers ?action] .
                }''' % (pred,obj)).execute(model):

            action = res['action'].uri
            matches = matches + 1
            self.fire_action(action)
            
        if matches == 0:
            log.debug("no commands matched %r %r" % (pred,obj))
        return matches

    def fire_action(self, action):
        model = self.model
        log.info("running action %s" % action)

        for res in RDF.SPARQLQuery(self.prefixes + '''
                SELECT ?light ?level
                WHERE {
                 <%s> room:lightLevel [room:light ?light; room:to ?level] .
                }''' % action).execute(model):
            self.do_lightlevel(res['light'].uri, res['level'])

        for res in RDF.SPARQLQuery(self.prefixes + '''
                SELECT ?command
                WHERE {
                 <%s> room:lightCommand ?command .
                }''' % action).execute(model):
            self.light_cmd(res['command'])

        for res in RDF.SPARQLQuery(self.prefixes + '''
                SELECT ?command
                WHERE {
                    <%s> room:execute ?command.
                }''' % action).execute(model):
            log.info("running %s" % str(res['command']))
            self.system_cmd(str(res['command']))

##         for res in RDF.SPARQLQuery(self.prefixes + '''
##                 SELECT ?command
##                 WHERE {
##                     <%s> room:execute ?command.
##                 }''' % action).execute(model):
##             log.info("running %s" % str(res['command']))
##             self.system_cmd(str(res['command']))

                    
    def do_lightlevel(self, light_uri, level):
        prefix = "http://projects.bigasterisk.com/room/lights/"
        lightname = str(light_uri)[len(prefix):]

        assert (level.literal_value['datatype'] ==
                RDF.Uri("http://www.w3.org/2001/XMLSchema#float"))
        level = float(level.literal_value['string'])

        self.set_light(lightname, level)
            
    def set_light(self, name, lev):
        log.info("%s to %s" % (name,lev))
        self.light_cmd("setLight", name, lev)

    def light_cmd(self, method, *args):
        if not hasattr(self, 'light_server'):
            uri = "http://dot:%s" % socket.getservbyname("lights","tcp")
            if not self.withTwisted:
                import xmlrpclib
                self.light_server = xmlrpclib.ServerProxy(uri)
            else:
                import twisted.web.xmlrpc
                self.light_server = twisted.web.xmlrpc.Proxy(uri)

        if not self.withTwisted:
            try:
                getattr(self.light_server, str(method))(*args)
            except xmlrpclib.Fault, e:
                self.xmlrpc_err("%s on command %s%r" % (e, method,tuple(args)))
        else:
            d = self.light_server.callRemote(method, *args)
            d.addErrback(self.xmlrpc_err)
            
    def xmlrpc_err(self, txt):
        log.error(txt)
        
    def system_cmd(self, cmd):
        ret = os.system(cmd)
        if ret != 0:
            log.error("command returned %d" % (ret >> 8))

    def mixer_cmd(self, channel, levels):
        m = alsaaudio.Mixer("Master")
#        m.getvolume()

        m.setvolume(90,alsaaudio.MIXER_CHANNEL_ALL)
