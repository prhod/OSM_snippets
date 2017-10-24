# coding: utf-8

import osmium
import datetime
import shapely.wkb as wkblib

wkbfab = osmium.geom.WKBFactory()


class StopsHandler(osmium.SimpleHandler):
    def __init__(self):
        osmium.SimpleHandler.__init__(self)
        self.start_date = datetime.datetime.strptime("01/07/2017", "%d/%m/%Y").replace(tzinfo=datetime.timezone.utc)
        self.stops = {}

    def node(self, n):
        #on prend public_transport = platform et highway=bus_stop

        if n.timestamp < self.start_date:
            pass
        elif ('public_transport' in n.tags and n.tags['public_transport'] == 'platform') and \
             ('highway' in n.tags and n.tags['highway'] == 'bus_stop') :
            wkb = wkbfab.create_point(n.location)
            point = wkblib.loads(wkb, hex=True)
            name = ""
            public_transport = ""
            highway = ""
            if "name" in n.tags:
                name = n.tags["name"]
            if "public_transport" in n.tags:
                public_transport = n.tags["public_transport"]
            if "highway" in n.tags:
                highway = n.tags["highway"]

            if not n.id in self.stops:
                self.stops[n.id] = {}
                self.stops[n.id]["version"] = []
                self.stops[n.id]["date"] = []
                self.stops[n.id]["name"] = []
                self.stops[n.id]["lat"] = []
                self.stops[n.id]["lon"] = []
                self.stops[n.id]["geometry"] = []
            self.stops[n.id]["version"].append(n.version)
            self.stops[n.id]["date"].append(n.timestamp)
            self.stops[n.id]["name"].append(name)
            self.stops[n.id]["lat"].append(n.location.lat)
            self.stops[n.id]["lon"].append(n.location.lon)
            self.stops[n.id]["geometry"].append(point)


class RelationHandler(osmium.SimpleHandler):
    def __init__(self):
        osmium.SimpleHandler.__init__(self)
        self.start_date = datetime.datetime.strptime("01/07/2017", "%d/%m/%Y").replace(tzinfo=datetime.timezone.utc)
        self.routes = {}

    def relation(self, r):
        #on prend type=route et route=bus
        if r.timestamp < self.start_date:
            pass
        elif ('type' in r.tags and r.tags['type'] == 'route') and ('route' in r.tags and r.tags['route'] == 'bus') :
            name = ""
            ref = ""
            r_type = ""
            route = ""
            if "ref" in r.tags:
                ref = r.tags["ref"]
            if "name" in r.tags:
                name = r.tags["name"]
            ways = []
            for rm in r.members:
                if not rm.type == 'w': continue
                ways.append(rm.ref)

            if not r.id in self.routes:
                self.routes[r.id] = {}
                self.routes[r.id]["version"] = []
                self.routes[r.id]["date"] = []
                self.routes[r.id]["ref"] = []
                self.routes[r.id]["name"] = []
                self.routes[r.id]["ways"] = []

            self.routes[r.id]["version"].append(r.version)
            self.routes[r.id]["date"].append(r.timestamp)
            self.routes[r.id]["ref"].append(ref)
            self.routes[r.id]["name"].append(name)
            #ways est un tableau qui contient, pour chaque version, un tableau de ways
            self.routes[r.id]["ways"].append(ways)


class WayHandler(osmium.SimpleHandler):
    def __init__(self, requested_ways):
        osmium.SimpleHandler.__init__(self)
        self.requested_ways = requested_ways
        self.ways = {}

    def way(self, w):
        if w.id in self.requested_ways:
            if not w.id in self.ways:
                self.ways[w.id] = {}
                self.ways[w.id]["object_id"] = w.id
                self.ways[w.id]["version"] = ""
                self.ways[w.id]["date"] = ""
                self.ways[w.id]["nodes_ref"] = ""
            if not self.ways[w.id]["version"] or self.ways[w.id]["version"] < w.version:
                self.ways[w.id]["version"] = w.version
                self.ways[w.id]["date"] = w.timestamp
                self.ways[w.id]["nodes_ref"] = [n.ref for n in w.nodes]


class NodeHandler(osmium.SimpleHandler):
    def __init__(self, requested_nodes):
        osmium.SimpleHandler.__init__(self)
        self.requested_nodes = requested_nodes
        self.nodes = {}

    def node(self, n):
        if n.id in self.requested_nodes:
            if not n.id in self.nodes:
                self.nodes[n.id] = {}
                self.nodes[n.id]["object_id"] = n.id
                self.nodes[n.id]["version"] = ""
                self.nodes[n.id]["lat"] = ""
                self.nodes[n.id]["lon"] = ""
                self.nodes[n.id]["valid"] = ""
            if not self.nodes[n.id]["version"] or self.nodes[n.id]["version"] < n.version:
                self.nodes[n.id]["version"] = n.version
                try:
                    if n.location.valid:
                        self.nodes[n.id]["lat"] = n.location.lat
                        self.nodes[n.id]["lon"] = n.location.lon
                    else:
                        print("point invalide : {:d}".format(n.id))
                except Exception as e:
                    print("exception sur le node {:d}".format(self.nodes[n.id]["object_id"]))
                    #raise
