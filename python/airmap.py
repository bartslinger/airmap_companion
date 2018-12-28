#!/usr/bin/env python3

import pathlib
import requests
import json
import datetime
import geojson
import time

import base64
import socket
import struct
from Crypto import Random
from Crypto.Cipher import AES

# generated file
import telemetry_pb2

import simulator

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
        self.flight = None
        self.comm = None

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

    def refresh_token(self):
        #url = "https://" + self.config['sso']['host'] + "/delegation"
        #payload = {
        #        'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
        #        'client_id': self.config['credentials']['oauth']['client-id'],
        #        'refresh_token': ''}
        # not finished yet
        pass

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
            self.flight = reply.json()["data"]
            pass
        else:
            print("error:")
            print(reply.json())
 
    def end_flight(self):
        url = "https://api.airmap.com/flight/v2/" + self.flight['flight_id'] + "/end"
        headers = {
                "Authorization": "Bearer " + self.token,
                "X-API-Key": self.config['credentials']['api-key']
                }
        reply = requests.post(url, headers=headers)
        if reply.json()["status"] == "success":
            print(reply.json())
        else:
            print("error:")
            print(reply.json())
        self.flight = None
        
    def start_comm(self):
        url = "https://api.airmap.com/flight/v2/" + self.flight['flight_id'] + "/start-comm"
        headers = {
                "Authorization": "Bearer " + self.token,
                "X-API-Key": self.config['credentials']['api-key']
                }
        reply = requests.post(url, headers=headers)
        if reply.json()["status"] == "success":
            self.comm = reply.json()["data"]
            print("comm started", self.comm["key"])
        else:
            print("error:")
            print(reply.json())

    def end_comm(self):
        url = "https://api.airmap.com/flight/v2/" + self.flight['flight_id'] + "/end-comm"
        headers = {
                "Authorization": "Bearer " + self.token,
                "X-API-Key": self.config['credentials']['api-key']
                }
        reply = requests.post(url, headers=headers)
        if reply.json()["status"] == "success":
            self.comm = reply.json()["data"]
        else:
            print("error:")
            print(reply.json())

class AirmapTelemetry:

    def __init__(self):
        self.config = None
        self.flight_id = None
        self.secret_key = None
        self.load_config()
        self.position = telemetry_pb2.Position()
        self.sock = None
        self.counter = 1

    def __del__(self):
        if self.sock != None:
            print("closing socket")
            self.sock.close()

    def get_timestamp(self):
        d = datetime.datetime.now()
        return int(d.microsecond/1000 + time.mktime(d.timetuple())*1000)

    def start(self, flight_id, comm_key):
        self.flight_id = flight_id
        self.secret_key = base64.b64decode(comm_key)
        HOSTNAME = self.config['telemetry']['host']
        IPADDR = socket.gethostbyname(HOSTNAME)
        PORTNUM = self.config['telemetry']['port']
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
        self.sock.connect((IPADDR, PORTNUM))

    def update_position(self, lat, lon, agl, msl, hacc):
        self.position.timestamp = self.get_timestamp()
        self.position.latitude = lat
        self.position.longitude = lon
        self.position.altitude_agl = agl
        self.position.altitude_msl = msl
        self.position.horizontal_accuracy = hacc

    def send_update(self):
        print("sending telemetry update %d" % self.counter)
        # serialize  protobuf messages to string and pack to payload buffer
        bytestring = self.position.SerializeToString()
        fmt = '!HH'+str(len(bytestring))+'s'
        payload = struct.pack(fmt, 1, len(bytestring), bytestring)

        # encrypt payload
        # use PKCS7 padding with block size 16
        BS = 16
        pad = lambda s: s + bytes((BS - len(s) % BS) * chr(BS - len(s) % BS), 'utf-8')
        payload = pad(payload)
        IV = Random.new().read(16)
        aes = AES.new(self.secret_key, AES.MODE_CBC, IV)
        encryptedPayload = aes.encrypt(payload)
        # send telemetry
        # packed data content of the UDP packet
        fmt = '!LB'+str(len(self.flight_id))+'sB16s'+str(len(encryptedPayload))+'s'
        PACKETDATA = struct.pack(fmt, self.counter, len(self.flight_id), bytes(self.flight_id, 'utf-8'), 1, IV, encryptedPayload)
        self.counter += 1

        # send the payload
        self.sock.send(PACKETDATA)

    def load_config(self, config=''):
        if config == '':
            config = pathlib.Path.home() / '.config/airmap/production/config.json'
        try:
            config_fp = open(config)
        except:
            print("could not open config file")

        self.config = json.load(config_fp)

        
if __name__ == "__main__":
    airmap = Airmap()
    airmap.login()
    airmap.get_pilot()

    sim = simulator.Simulator()
    if 1:
        # submit flightplan

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
        airmap.start_comm()

        telem = AirmapTelemetry()
        telem.start(airmap.flight['flight_id'], airmap.comm['key'])
        
        counter = 1
        for i in range(20):

            telem.update_position(sim.getLattitude(), sim.getLongtitude(), sim.getAgl(), sim.getMsl(), sim.getHorizAccuracy())
            telem.send_update()

            # print timestamp when payload was sent
            print("Sent payload messsage #" , counter ,  "@" , time.strftime("%H:%M:%S"))
            
            # increment sequence number
            counter += 1

            # 5 Hz
            time.sleep(0.2)

        airmap.end_comm()
        airmap.end_flight()
