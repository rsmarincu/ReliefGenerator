from flask import Flask, render_template, request, jsonify
import math
import requests
import numpy as np
import pandas
import json
import utm
from geopy.geocoders import Nominatim
import configparser

configs = configparser.RawConfigParser()
configs.read('./api.ini')

apiKey = configs['DEFAULT']['API_KEY']
app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

geolocator = Nominatim(user_agent='rsmarincu')

# //variables..................................................

earthR=6371000
west=math.radians(270)
north=math.radians(0)

latitude = 45.832119
longitude = 6.865575
size = 100
distance = 50
increase = 350

# //Routes...................................

@app.route('/')
def main():
    return render_template('main.html')

@app.route('/hello',methods=['GET','POST'])
def hello():
    if request.method == 'POST':
        print(request.get_json())
        json = request.get_json()
        location = json['location']
        size = int(json['size'])
        distance = int(json['distance'])
        coordinates = geolocator.geocode(location,timeout=10)
        latitude = coordinates.latitude
        longitude = coordinates.longitude
        sendData = createData(size, latitude,longitude, distance)
        return jsonify(sendData)
    else:
        return 'nothing'



# //Definitions.................................

def getPointWest(initialLat,initialLong,distance):
    initialLat = math.radians(initialLat)
    initialLong = math.radians(initialLong)
    newLat = math.asin(math.sin(initialLat) * math.cos(distance/earthR) + math.cos(initialLat) * math.sin(distance/earthR) * math.cos(west))
    newLong = initialLong + math.atan2(math.sin(west) * math.sin(distance/earthR) * math.cos(initialLat) , math.cos(distance/earthR) - math.sin(initialLat)* math.sin(newLat))
    newLat = math.degrees(newLat)
    newLong = math.degrees(newLong)
    location=(newLat,newLong)
    return location


def getPointNorth(initialLat,initialLong,distance):
    initialLat = math.radians(initialLat)
    initialLong = math.radians(initialLong)
    newLat = math.asin(math.sin(initialLat) * math.cos(distance/earthR) + math.cos(initialLat) * math.sin(distance/earthR) * math.cos(north))
    newLong = initialLong + math.atan2(math.sin(north) * math.sin(distance/earthR) * math.cos(initialLat) , math.cos(distance/earthR) - math.sin(initialLat)* math.sin(newLat))
    newLat = math.degrees(newLat)
    newLong = math.degrees(newLong)
    location=(newLat,newLong)
    return location


def createGrid(size,lat,long,dist):
    tuple_=()
    points=np.empty(shape=(size,size),dtype=tuple)
    northDist=0
    westDist=0
    for i in range(0,size):
        points[i,0]=getPointNorth(lat,long,northDist)
        nLat=points[i,0][0]
        nLong=points[i,0][1]
        for j in range(0,size):
            points[i,j]=getPointWest(nLat,nLong,westDist)
            westDist+=dist
        westDist=0
        northDist+=dist
    return points


def getElevations(points):
    points = points.flatten()
    locations = ''
    elevations = []
    counter = increase

    _url = 'https://maps.googleapis.com/maps/api/elevation/json?locations={}&key={}'

    for i,point in enumerate (points):

        newS = '{},{}'.format(point[0],point[1])
        locations = locations + newS + '|'

        if i == counter:
            locations = locations[:-1]
            r = requests.get(_url.format(locations,apiKey))
            results= json.loads(r.content)
            for result in results['results']:
                elevations.append(result['elevation'])
            locations = ''
            counter += increase
        elif i == len(points)-1:
            locations = locations[:-1]
            r = requests.get(_url.format(locations,apiKey))
            results= json.loads(r.content)
            for result in results['results']:
                elevations.append(result['elevation'])

    return elevations

def createXYgrid(size,dist):
    grid = np.empty(shape=(size,size),dtype=tuple)
    x = 0
    y = 0
    for i in range(0,size):
        grid [i,0] = (x,y)
        for j in range(0,size):
            grid[i,j] = (x,y)
            y+=dist
        y = 0
        x+=dist
    return grid


def createData(size,latitude,longitude,distance):

    coordinates=createGrid(size,latitude,longitude,distance)
    grid = createXYgrid(size,distance)
    grid = grid.flatten().tolist()
    elevations = getElevations(coordinates)
    lleList = []
    minElevation = 650000
    maxElevation = -650000
    for i,elev in enumerate (elevations):
        if elev <  minElevation:
            minElevation = elev
        if elev > maxElevation:
            maxElevation = elev
        dict = {'lat':grid[i][0],
                'long':grid[i][1],
                'elev':elev}
        lleList.append(dict)

    lleJson = {'coordinate':lleList,
                'lowest':minElevation,
                'size': size,
                'distance':distance,
                'highest': maxElevation
                }
    return lleJson
