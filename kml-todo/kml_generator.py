﻿import requests
import json





if __name__ == '__main__':
    overpass_base_url = 'http://overpass-api.de/api/interpreter?data='
    overpass_url = overpass_base_url + '[out:json][timeout:125];area(3600008649)->.area;node["highway"="bus_stop"][!"name"](area.area);out skel;'
    #overpass_url = overpass_base_url + '[out:json][timeout:125];area(3600402773)->.area;node["highway"="bus_stop"][!"name"](area.area);out skel;'

    overpass_call = requests.get(overpass_url)
    if overpass_call.status_code != 200:
        print ("KO à l'appel Overpass")
        exit(1)
    overpass_result = overpass_call.json()

    kml_wrapper = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://earth.google.com/kml/2.2">
<Document>
  <Style id="placemark-blue">
    <IconStyle>
      <Icon>
        <href>http://mapswith.me/placemarks/placemark-blue.png</href>
      </Icon>
    </IconStyle>
  </Style>
  <Style id="placemark-brown">
    <IconStyle>
      <Icon>
        <href>http://mapswith.me/placemarks/placemark-brown.png</href>
      </Icon>
    </IconStyle>
  </Style>
  <Style id="placemark-green">
    <IconStyle>
      <Icon>
        <href>http://mapswith.me/placemarks/placemark-green.png</href>
      </Icon>
    </IconStyle>
  </Style>
  <Style id="placemark-orange">
    <IconStyle>
      <Icon>
        <href>http://mapswith.me/placemarks/placemark-orange.png</href>
      </Icon>
    </IconStyle>
  </Style>
  <Style id="placemark-pink">
    <IconStyle>
      <Icon>
        <href>http://mapswith.me/placemarks/placemark-pink.png</href>
      </Icon>
    </IconStyle>
  </Style>
  <Style id="placemark-purple">
    <IconStyle>
      <Icon>
        <href>http://mapswith.me/placemarks/placemark-purple.png</href>
      </Icon>
    </IconStyle>
  </Style>
  <Style id="placemark-red">
    <IconStyle>
      <Icon>
        <href>http://mapswith.me/placemarks/placemark-red.png</href>
      </Icon>
    </IconStyle>
  </Style>
  <Style id="placemark-yellow">
    <IconStyle>
      <Icon>
        <href>http://mapswith.me/placemarks/placemark-yellow.png</href>
      </Icon>
    </IconStyle>
  </Style>
  <name>Arrêts de bus sans nom</name>
  <visibility>1</visibility>
    """

    for elem in overpass_result['elements']:
        kml_template = """
      <Placemark>
        <name>Compléter le nom de cet arrêt de bus</name>
        <styleUrl>#placemark-blue</styleUrl>
        <Point><coordinates>%%kml_lon%%,%%kml_lat%%</coordinates></Point>
      </Placemark>"""

        kml_template = kml_template.replace("%%kml_lat%%", str(elem['lat']))
        kml_template = kml_template.replace("%%kml_lon%%", str(elem['lon']))
        kml_wrapper += kml_template

    kml_wrapper += """
</Document>
</kml>
    """
    print (kml_wrapper)
