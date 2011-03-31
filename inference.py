"""
see ./reasoning for usage
"""

import sys, re
import restkit
from rdflib import StringInputSource
from rdflib.Graph import Graph

sys.path.append("/my/proj/room/fuxi/build/lib.linux-x86_64-2.6")
from FuXi.Rete.Util import generateTokenSet
from FuXi.Rete import ReteNetwork
from rdflib import plugin
from rdflib.store import Store

def parseTrig(trig):
    """
    yields quads
    """
    m = re.match(r"<([^>]+)> \{(.*)\}\s*$", trig, re.DOTALL)
    if m is None:
        raise NotImplementedError("trig format was too tricky")
        
    ctx = m.group(1)
    n3 = m.group(2)
    g = Graph()
    g.parse(StringInputSource(n3), format="n3")
    for stmt in g:
        yield stmt + (ctx,)

def infer(graph, rules):
    """
    returns new graph of inferred statements
    """
    # based on fuxi/tools/rdfpipe.py
    store = plugin.get('IOMemory',Store)()        
    store.open('')

    target = Graph()
    tokenSet = generateTokenSet(graph)
    network = ReteNetwork(rules, inferredTarget=target)
    network.feedFactsToAdd(tokenSet)

    store.rollback()
    return target

def addTrig(graph, url):
    trig = restkit.request(url).body_string()
    graph.addN(parseTrig(trig))
