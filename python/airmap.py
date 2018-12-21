#!/usr/bin/env python3

import pathlib
import requests
import json
import datetime
import geojson

class AirmapFlightplan:

    def __init__(self):
        self.geometry = ''
        self.takeoff_latitude = ''
        self.takeoff_longitude = ''
        self.max_altitude_agl = 0.
        self.pilot_id = ''
        self.start_time = ''
        self.end_time = ''
        self.buffer = '1'

class Airmap:

    def __init__(self, config=''):
        self.token = ''
        self.config = None
        self.load_config(config)
        self.pilot = None
        self.flightplan = None

    def load_config(self, config=''):
        if config == '':
            config = pathlib.Path.home() / '.config/airmap/production/config.json'
        try:
            config_fp = open(config)
        except:
            print("could not open config file")

        self.config = json.load(config_fp)

    def login(self):
        url = "https://" + self.config['sso']['host'] + "/oauth/ro"
        payload = {
              'grant_type': 'password',
              'client_id': self.config['credentials']['oauth']['client-id'],
              'connection': 'Username-Password-Authentication',
              'username': self.config['credentials']['oauth']['username'],
              'password': self.config['credentials']['oauth']['password'],
              'scope': 'openid offline_access',
              'device': self.config['credentials']['oauth']['device-id'] 
        }
        reply = requests.post(url, json=payload)
        print(reply.status_code)
        self.token = reply.json()["id_token"]
        print(self.token)

    def get_pilot(self):
        url = "http://api.airmap.com/pilot/v2/profile"
        headers = {
                "Authorization": "Bearer " + self.token,
                "X-API-Key": self.config['credentials']['api-key']
                }
        reply = requests.get(url, headers=headers)
        if reply.json()["status"] == "success":
            self.pilot = reply.json()["data"]
        else:
            print("error:")
            print(reply.json())

    def refresh_token():
        url = "https://" + self.config['sso']['host'] + "/delegation"
        payload = {
                'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
                'client_id': self.config['credentials']['oauth']['client-id'],
                'refresh_token': ''}
        # not finished yet

    def create_flightplan(self, flightplan):
        url = "https://api.airmap.com/flight/v2/plan"
        headers = {
                "Content-Type": "application/json; charset=utf-8",
                "Authorization": "Bearer " + self.token,
                "X-API-Key": self.config['credentials']['api-key']
                }
        data = {
                "start_time": flightplan.start_time,
                "end_time": flightplan.end_time,
                "max_altitude_agl": flightplan.max_altitude_agl,
                "takeoff_latitude": flightplan.takeoff_latitude,
                "takeoff_longitude": flightplan.takeoff_longitude,
                "buffer": flightplan.buffer,
                "geometry": flightplan.geometry,
                "pilot_id": flightplan.pilot_id
                }
        reply = requests.post(url, json=data, headers=headers)
        print(headers)
        print(json.dumps(data, indent=4))
        if reply.json()["status"] == "success":
            self.flightplan = reply.json()["data"]
            print(self.flightplan)
        else:
            print("error:")
            print(reply.json())

    def submit_flight(self):
        url = "https://api.airmap.com/flight/v2/plan/" + self.flightplan['id'] + "/submit"
        print(url)
        headers = {
                "Content-Type": "application/json; charset=utf-8",
                "Authorization": "Bearer " + self.token,
                "X-API-Key": self.config['credentials']['api-key']
                }
        data = {'public': True}
        reply = requests.post(url, headers=headers, json=data)
        if reply.json()["status"] == "success":
            print(reply.json())
            pass
        else:
            print("error:")
            print(reply.json())
 
        
if __name__ == "__main__":
    airmap = Airmap()
    airmap.login()
    airmap.get_pilot()

    flightplan = AirmapFlightplan()
    latitude = 52.168014
    longitude = 4.412414
    flightplan.takeoff_latitude = str(latitude)
    flightplan.takeoff_longitude = str(longitude)

    p = geojson.Point((longitude, latitude))
    flightplan.geometry = geojson.Point((longitude, latitude))

    flightplan.max_altitude_agl = 50.
    flightplan.pilot_id = airmap.pilot['id']
    now = datetime.datetime.now(datetime.timezone.utc)
    flightplan.start_time = now.isoformat()
    flight_time = datetime.timedelta(minutes=20)
    flightplan.end_time = (now + flight_time).isoformat() 
    airmap.create_flightplan(flightplan)
    
    airmap.submit_flight()
