# coding: utf-8

# Export des données Transport du Ghana

#nécessite phantomjs (https://gist.github.com/julionc/7476620) et selenium (sudo pip3 install selenium)

import os
import requests

import datetime
import osmium
import pandas as pd
from shapely.geometry import LineString, MultiLineString
from shapely.ops import cascaded_union
import ghana_transit_to_gif_handlers



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


#===============================================
#              Load Stops
stops_file = './stops.csv'
stops = []
if not os.path.isfile(stops_file):
    print("Le fichier {} n'existe pas, lancement du traitement".format(stops_file))
    stops_handler = ghana_transit_to_gif_handlers.StopsHandler()
    stops_handler.apply_file(dest_file)

    #on charge dans stops les données finales, avec la 1ère date de modification après le 1er juillet 2017
    #et le dernier nom et la dernière position connus
    for k,v in stops_handler.stops.items():
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
        stops.append(s)

    pd.DataFrame.from_dict(stops).to_csv('./stops.csv')
else:
    print("Le fichier {} existe, chargement depuis le fichier".format(stops_file))
    stops = pd.read_csv(stops_file).to_dict(orient="records")
print('fin de chargement des stops : {:d}'.format(len(stops)))

#===============================================
#              Load Relations
routes_file1 = "./routes.csv"
routes = []
routes_all_ways = []
if not os.path.isfile(routes_file1):
    print("Le fichier {} n'existe pas, lancement de la lecture des relations".format(routes_file1))
    routes_handler = ghana_transit_to_gif_handlers.RelationHandler()
    routes_handler.apply_file(dest_file)

    for k,v in routes_handler.routes.items():
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
        routes.append(r)

    #il faut ensuite charger les dernières versions des ways utilisés par les relations pour avoir la géometrie
    pd_routes = pd.DataFrame.from_dict(routes)
    pd_routes.to_csv('./routes.csv')
else:
    print("Le fichier {} existe, chargement depuis le fichier".format(routes_file1))
routes = pd.read_csv(routes_file1, parse_dates=["creation_date"]).to_dict(orient="records")
for r in routes:
    #liste stockée comme chaine de caractères => on la parse à la main (plus simple)
    ways = r["last_ways"][1:-1]
    ways = ways.split(",")
    ways = [int(i) for i in ways if i]
    r["last_ways"] = ways
    routes_all_ways.extend(ways)
print('fin de chargement des relations : {:d} (dont {:d} références de ways)'.format(len(routes), len(routes_all_ways)))


#===============================================
#              Load Ways
ways_file = "./ways.csv"
ways_all_nodes = []
routes_all_ways = set(routes_all_ways) #utilisation d'un set pour sacrément accélerer la vérif de présence d'un item /!\
if not os.path.isfile(ways_file):
    print("Le fichier {} n'existe pas, lancement de la lecture des ways".format(ways_file))
    way_handler = ghana_transit_to_gif_handlers.WayHandler(routes_all_ways)
    way_handler.apply_file(dest_file)
    print("Ecriture du fichier {}".format(ways_file))
    ways = [w for w in way_handler.ways.values()]
    pd.DataFrame.from_dict(ways).to_csv(ways_file)
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


#===============================================
#              Load Nodes
#pas de sauvegarde fichier pour les nodes, le chargement est rapide
ways_all_nodes = set(ways_all_nodes)
routes_handler3 = ghana_transit_to_gif_handlers.NodeHandler(ways_all_nodes)
routes_handler3.apply_file(dest_file)
nodes = routes_handler3.nodes
print("Chargement des nodes terminé : {:d}".format(len(nodes)))


#===============================================
print("Construction des géometries des ways")
for w in ways:
    w_nodes = []
    for wn in w["nodes_ref"]:
        n = nodes[wn]
        w_nodes.append((n["lat"], n["lon"]))
    w["geom_raw"] = w_nodes
    w["geom"] = LineString(w_nodes)

#===============================================
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


#===============================================
print("Chargement de la carte")
import folium
from folium.plugins import MarkerCluster
from IPython.display import Image
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

def show_date_on_image(image_path, date_to_display):
    print("modification de l'image")
    img = Image.open(image_path)
    draw = ImageDraw.Draw(img)

    text_offset = [img.size[0] - 200, img.size[1] - 50]
    text_border = 4
    text_length = 119
    text_size = 20
    draw.rectangle([
        text_offset[0] - text_border,
        text_offset[1] - text_border,
        text_offset[0] + text_border + text_length,
        text_offset[1] + text_border + text_size
        ], fill='#858687')

    font = ImageFont.truetype('Pillow/Tests/fonts/LiberationMono-Bold.ttf', text_size)
    draw.text((text_offset[0], text_offset[1]), date_to_display.strftime('%Y-%m-%d'),'#000000',font=font)
    img.save(image_path)

attributions = "cartodb | OSM"
tiles = 'https://cartodb-basemaps-{s}.global.ssl.fastly.net/dark_all/{z}/{x}/{y}.png'
m = folium.Map(location=[5.6204,-0.2125], zoom_start=12, attr=attributions, tiles=tiles, png_enabled=True)

img_tmp_dir = './images'
if not os.path.exists(img_tmp_dir):
    os.makedirs(img_tmp_dir)

start_date = datetime.datetime.strptime('2017-07-15', '%Y-%m-%d')
end_date = datetime.datetime.strptime('2017-09-06', '%Y-%m-%d')
delta_days = 5
date_cursor = start_date
for r in routes:
    r["displayed"] = False
while date_cursor <= end_date:
    for r in routes:
        if not r["displayed"] and r["creation_date"] < pd.to_datetime(date_cursor):
            folium.PolyLine(r["geom_raw"], color="red", weight=1.5, opacity=1).add_to(m)
            r["displayed"] = True
    print("Enregistrement de la carte pour la date du {}".format(date_cursor.strftime('%Y-%m-%d')))
    image_path = os.path.join(img_tmp_dir, "image_{}.png".format(date_cursor.strftime('%Y-%m-%d')))
    with open(image_path, "wb")  as image_file:
        m._png_image = None #on réinitialise le PNG
        image_file.write(m._to_png())
    show_date_on_image(image_path, date_cursor)
    date_cursor = date_cursor + datetime.timedelta(days=delta_days)

#===============================================
print("Création du GIF")
import imageio

file_names = sorted((os.path.join(img_tmp_dir, fn) for fn in os.listdir(img_tmp_dir) if fn.endswith('.png')))

with imageio.get_writer('final.gif', mode='I', duration=0.4) as writer:
    for filename in file_names:
        image = imageio.imread(filename)
        writer.append_data(image)
