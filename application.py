import time
from flask import Flask, request, render_template
from flask_caching import Cache
import requests
import olakeys as olakeys
import urllib.parse
from geopy.distance import great_circle

application = Flask(__name__)

api_key = olakeys.api_key
request_id = olakeys.request_id
gmap_api_key = olakeys.gmap_api_key

def get_coordinates(address):
    url = f"https://api.olamaps.io/places/v1/geocode?address={address}&api_key={api_key}"
    headers = {"X-Request-Id": request_id, "Accept": "application/json"}
    response = requests.get(url, headers=headers)
   
    #response = requests.get(url,headers={"X-Request-Id":request_id})
    if response.status_code == 200:
        data = response.json()
        if 'geocodingResults' in data and len(data['geocodingResults'])>0:
            first_result = data['geocodingResults'][0]
            geometry = first_result.get('geometry',{})
            location = geometry.get('location', {})
            lat = location.get('lat')
            lng = location.get('lng')
            return lat,lng
        else:
            return 200,200 
    else:
        return None

# Olamaps distance and time
def get_oladistance(source_lat, source_lng, destination_lat, destination_lng):
    origin = f"{source_lat},{source_lng}"
    destination = f"{destination_lat},{destination_lng}"

    origin_encoded = urllib.parse.quote(origin)
    destination_encoded = urllib.parse.quote(destination)

    #url = f"https://api.olamaps.io/routing/v1/directions?origin={origin_encoded}&destination={destination_encoded}&mode=driving&alternatives=false&steps=false&overview=full&language=en&traffic_metadata=false&api_key={api_key}"
    
    url = f"https://api.olamaps.io/routing/v1/distanceMatrix?origins={origin_encoded}&destinations={destination_encoded}&api_key={api_key}"
    headers = {"Accept": "application/json"}
    response = requests.get(url,headers=headers)
    if response.status_code == 200:
        data = response.json()
        if data is not None and 'rows' in data and len(data['rows']) > 0:
            distance = data['rows'][0]['elements'][0]['distance']/1000  #to Kilometers
            time = data['rows'][0]['elements'][0]['duration']
            mm, ss = divmod(time, 60)
            hh, mm = divmod(mm, 60)
            time = str(hh)+ "hr "+ str(mm)+ 'min '+ str(ss)+"sec."
            return distance,time
        else:
            return None
    else:
        return None

# Google maps distance and time.

def get_googledistance(source_lat, source_lng, destination_lat, destination_lng):
    origin = f"{source_lat},{source_lng}"
    destination = f"{destination_lat},{destination_lng}"

    url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={origin}&destinations={destination}&mode=driving&language=en&key={gmap_api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data is not None and 'rows' in data and len(data['rows']) > 0:
            distance = data['rows'][0]['elements'][0]['distance']['value'] / 1000  # Convert meters to kilometers
            time = data['rows'][0]['elements'][0]['duration']['value']  # In seconds
            mm, ss = divmod(time, 60)
            hh, mm = divmod(mm, 60)
            time = str(hh)+ "hr "+ str(mm)+ 'min '+ str(ss)+"sec."
            return distance, time
        else:
            return None
    else:
        return None


@application.route('/',methods=['GET','POST'])

def index():
    distance = None
    ola_distance = None
    ola_time = 0
    source_coords = None
    destination_coords = None
    source_address = ""
    destination_address = ""
    source_lat, source_lng, destination_lat, destination_lng,google_distance, google_time = None, None, None, None,None,None
    if request.method == 'POST':
        source_address = request.form['source']
        destination_address = request.form['destination'] 
        source_lat, source_lng = get_coordinates(source_address)  
        destination_lat, destination_lng = get_coordinates(destination_address)
        if(source_lat == 200 or source_lng == 200):
            return render_template('index.html',sourceError='Unable to find source location')
        elif(destination_lat == 200 or destination_lng == 200):
            return render_template('index.html',destinationError='Unable to find source location')
        else:
            
            

            if source_lat is not None and destination_lat is not None:
                source_coords = (source_lat, source_lng)
                destination_coords = (destination_lat, destination_lng)
                distance = great_circle(source_coords, destination_coords).kilometers
                ola_distance,ola_time = get_oladistance(source_lat, source_lng, destination_lat, destination_lng)
                google_distance, google_time = get_googledistance(source_lat, source_lng, destination_lat, destination_lng)        
    if source_address is not None:
        return render_template('index.html',distance=distance, ola_distance=ola_distance, source = source_address, destination = destination_address, 
                           source_lat=source_lat, source_long=source_lng, dest_lat=destination_lat,dest_long=destination_lng, ola_time=ola_time,
                            google_distance=google_distance, google_time=google_time)
    else:
        return None

if __name__ == '__main__':
    application.run(debug=True)
