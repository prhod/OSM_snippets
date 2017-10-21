
# coding: utf-8

# ## Export des données Transport du Ghana

# In[1]:


import os
import requests

url_source = 'http://download.geofabrik.de/africa/ghana.osh.pbf'
dest_file = './ghana.osh.pbf'
if not os.path.isfile(dest_file):
    print("Downloading {}".format(dest_file))
    with open(dest_file, "wb") as file:
        r = requests.get(url_source)
        file.write(r.content)
    print("Downloaded !")
else:
    print("File {} already exists".format(dest_file))



# In[2]:


import datetime
import osmium
import pandas as pd
import shapely.wkt as wktlib
import shapely.wkb as wkblib

wkbfab = osmium.geom.WKBFactory()

class StopsHandler(osmium.SimpleHandler):
    def __init__(self):
        osmium.SimpleHandler.__init__(self)
        self.start_date = datetime.datetime.strptime("01/07/2017", "%d/%m/%Y").replace(tzinfo=datetime.timezone.utc)

    def node(self, n):
        #on prend public_transport = platform et highway=bus_stop

        if n.timestamp < self.start_date:
            pass
        elif ('public_transport' in n.tags and n.tags['public_transport'] == 'platform') and             ('highway' in n.tags and n.tags['highway'] == 'bus_stop') :
            #print(dir(n.location))
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

            if not n.id in stops:
                stops[n.id] = {}
                stops[n.id]["version"] = []
                stops[n.id]["date"] = []
                stops[n.id]["name"] = []
                stops[n.id]["geometry"] = []
            stops[n.id]["version"].append(n.version)
            stops[n.id]["date"].append(n.timestamp)
            stops[n.id]["name"].append(name)
            stops[n.id]["geometry"].append(point)

stops_file = './stops.csv'
stops = {}
stops_tmp = []
if not os.path.isfile(stops_file):
    print("Le fichier {} n'existe pas, lancement du traitement".format(stops_file))
    stops_handler = StopsHandler()
    stops_handler.apply_file(dest_file)

    #on charge dans stops_tmp les données finales, avec la 1ère date de modification après le 1er juillet 2017
    #et le dernier nom et la dernière position connus
    for k,v in stops.items():
        min_version = min(v["version"])
        min_index = v["version"].index(min_version)
        max_version = max(v["version"])
        max_index = v["version"].index(max_version)
        s = {
             "object_id": k,
             "creation_date": v["date"][min_index],
             "last_modif_date": v["date"][max_index],
             "last_name": v["name"][max_index],
             "last_geometry": v["geometry"][max_index]
            }
        stops_tmp.append(s)

    pd.DataFrame.from_dict(stops_tmp).to_csv('./stops.csv')
else:
    print("Le fichier {} existe, chargement depuis le fichier".format(stops_file))
    stops_tmp = pd.read_csv(stops_file).to_dict(orient="records")
print('fin de chargement des stops : {:d}'.format(len(stops_tmp)))

# In[3]:


import datetime
import osmium
import pandas as pd

class RoutesHandler(osmium.SimpleHandler):
    def __init__(self):
        osmium.SimpleHandler.__init__(self)
        self.start_date = datetime.datetime.strptime("01/07/2017", "%d/%m/%Y").replace(tzinfo=datetime.timezone.utc)

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

            if not r.id in routes:
                routes[r.id] = {}
                routes[r.id]["version"] = []
                routes[r.id]["date"] = []
                routes[r.id]["ref"] = []
                routes[r.id]["name"] = []
                routes[r.id]["ways"] = []

            routes[r.id]["version"].append(r.version)
            routes[r.id]["date"].append(r.timestamp)
            routes[r.id]["ref"].append(ref)
            routes[r.id]["name"].append(name)
            #ways est un tableau qui contient, pour chaque version, un tableau de ways
            routes[r.id]["ways"].append(ways)

routes_file1 = "./routes.csv"
routes_tmp = []
routes_all_ways = []
if not os.path.isfile(routes_file1):
    print("Le fichier {} n'existe pas, lancement de la lecture des relations".format(routes_file1))
    routes = {}
    routes_handler = RoutesHandler()
    routes_handler.apply_file(dest_file)

    for k,v in routes.items():
        min_version = min(v["version"])
        min_index = v["version"].index(min_version)
        max_version = max(v["version"])
        max_index = v["version"].index(max_version)
        r = {
             "object_id": k,
             "creation_date": v["date"][min_index],
             "last_modif_date": v["date"][max_index],
             "last_ref": v["ref"][max_index],
             "last_name": v["name"][max_index],
             "last_ways": v["ways"][max_index]
            }
        routes_all_ways.extend(r["last_ways"])
        routes_tmp.append(r)

    #il faut ensuite charger les dernières versions des ways utilisés par les relations pour avoir la géometrie
    pd_routes = pd.DataFrame.from_dict(routes_tmp)
    pd_routes.to_csv('./routes.csv')
else:
    print("Le fichier {} existe, chargement depuis le fichier".format(routes_file1))
    routes_tmp = pd.read_csv(routes_file1).to_dict(orient="records")
    for r in routes_tmp:
        #liste stockée comme chaine de caractères => on la parse à la main (plus simple)
        ways = r["last_ways"][1:-1]
        ways = ways.split(",")
        ways = [int(i) for i in ways if i]
        r["last_ways"] = ways
        routes_all_ways.extend(ways)
routes = routes_tmp
print('fin de chargement des relations : {:d} (dont {:d} références de ways)'.format(len(routes), len(routes_all_ways)))
# In[ ]:

import osmium
from copy import deepcopy
import shapely.wkt as wktlib
import shapely.wkb as wkblib
wkbfab = osmium.geom.WKBFactory()

class RoutesHandler2(osmium.SimpleHandler):
    def __init__(self):
        osmium.SimpleHandler.__init__(self)
        self.print_step = 1000000
        self.last_print_id = -1
        self.starttime = datetime.datetime.now()

    def way(self, w):
        if w.id > self.last_print_id + self.print_step:
            print("reading way id = {:d} (actually {:d} ways kept)".format(w.id, len(ways)))
            print(datetime.datetime.now() - self.starttime)
            self.last_print_id = w.id
        if w.id in routes_all_ways:
            if not w.id in ways_all_nodes:
                ways[w.id] = {}
                ways[w.id]["object_id"] = w.id
                ways[w.id]["version"] = ""
                ways[w.id]["date"] = ""
                ways[w.id]["nodes_ref"] = ""
                #ways[w.id]["geom"] = []
            if not ways[w.id]["version"] or ways[w.id]["version"] < w.version:
                ways[w.id]["version"] = w.version
                ways[w.id]["date"] = w.timestamp
                ways[w.id]["nodes_ref"] = [n.ref for n in w.nodes]
                ways_all_nodes.extend(ways[w.id]["nodes_ref"])

                    # try:
                    #    wkb = wkbfab.create_linestring(w.nodes)
                    #    geom = wkblib.loads(wkb, hex=True)
                    # except:
                    #    print("create_linestring error with way {:d}".format(w.id))
                    #    geom = ''
                    # ways[w.id]["geom"] = geom

ways_file = "./ways.csv"
ways = {}
ways_all_nodes = []
routes_all_ways = set(routes_all_ways) #utilisation d'un set pour sacrément accélerer la vérif de présence d'un item /!\
if not os.path.isfile(ways_file):
    print("Le fichier {} n'existe pas, lancement de la lecture des ways".format(ways_file))
    routes_handler2 = RoutesHandler2()
    routes_handler2.apply_file(dest_file)
    print("Ecriture du fichier {}".format(ways_file))
    ways_tmp = [w for w in ways.values()]
    pd.DataFrame.from_dict(ways_tmp).to_csv(ways_file)
else:
    print("Le fichier {} existe, chargement depuis le fichier".format(ways_file))
    ways = pd.read_csv(ways_file).to_dict(orient="records")
    for w in ways:
        points = w["nodes_ref"][1:-1]
        points = points.split(",")
        points = [int(i) for i in points if i]
        ways_all_nodes.extend(points)
        w["nodes_ref"] = points
print("Chargement des ways terminé : {:d}".format(len(ways)))
print("nombre de refs de node : {:d}".format(len(ways_all_nodes)))

class RoutesHandler3(osmium.SimpleHandler):
    def __init__(self):
        osmium.SimpleHandler.__init__(self)

    def node(self, n):
        if n.id in ways_all_nodes:
            if not n.id in nodes:
                nodes[n.id] = {}
                nodes[n.id]["object_id"] = n.id
                nodes[n.id]["version"] = ""
                nodes[n.id]["lat"] = ""
                nodes[n.id]["lon"] = ""
                nodes[n.id]["valid"] = ""
            if not nodes[n.id]["version"] or nodes[n.id]["version"] < n.version:
                nodes[n.id]["version"] = n.version
                try:
                    if n.location.valid:
                        nodes[n.id]["lat"] = n.location.lat
                        nodes[n.id]["lon"] = n.location.lon
                    else:
                        print("point invalide : {:d}".format(n.id))
                except Exception as e:
                    print("exception sur le node {:d}".format(nodes[n.id]["object_id"]))
                    #raise
            # if len(nodes) % 1000 == 0:
            #     print(len(nodes))

#pas de sauvegarde fichier pour les nodes, le chargement est rapide
nodes = {}
ways_all_nodes = set(ways_all_nodes)
routes_handler3 = RoutesHandler3()
routes_handler3.apply_file(dest_file)
print("Chargement des nodes terminé : {:d}".format(len(nodes)))

from shapely.geometry import LineString, MultiLineString
from shapely.ops import cascaded_union

print("Construction des géometries des ways")
for w in ways:
    w_nodes = []
    for wn in w["nodes_ref"]:
        n = nodes[wn]
        w_nodes.append((n["lat"], n["lon"]))
    w["geom_raw"] = w_nodes
    w["geom"] = LineString(w_nodes)

print("Construction des géometries des relations")
for r in routes:
    r_ways = []
    r_ways_geom = []
    for rw in r["last_ways"]:
        for w in ways:
            if w["object_id"] == rw:
                r_ways.append(w["geom_raw"])
                r_ways_geom.append(w["geom"])
                break
    r["geom_raw"] = r_ways
    r["geom"] = MultiLineString(r_ways_geom)


print("Chargement de la carte")
import folium
from folium.plugins import MarkerCluster
from IPython.display import Image

m = folium.Map(location=[5.6064530999999995,-0.1773089], zoom_start=12, tiles='Cartodb Positron')
for r in routes:
    folium.PolyLine(r["geom_raw"], color="red", weight=2.5, opacity=1).add_to(m)

print("Enregistrement de la carte")
from IPython.display import Image
with open("./image.png", "wb")  as image_file:
    image_file.write(m._to_png())
