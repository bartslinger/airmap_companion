#!/usr/bin/env python3

import asyncio

import pymavlink.mavutil as mavutil
import pymavlink.dialects.v20.common as mavlink
import sys
import time
import signal

from airmap import Airmap, AirmapTelemetry, AirmapFlightplan
import geojson
import datetime

if len(sys.argv) != 4:
    print("Usage: %s <ip:udp_port> <system-id> <target-system-id>" %
          (sys.argv[0]))
    print(
        "Send mavlink pings, using given <system-id> and <target-system-id>, "
        "to specified interface")
    quit()

mav = mavutil.mavlink_connection(
    'udpin:' + sys.argv[1], source_system=int(sys.argv[2]))

mav.wait_heartbeat()
#print("Got first heartbeat")
loop = asyncio.get_event_loop()

airmap = Airmap()
telem = AirmapTelemetry()

class Vehicle:
    def __init__(self):
        self.state = 'idle'
        self.armed = False

    def parse_heartbeat(self, msg):
        armed = (msg.base_mode & mavlink.MAV_MODE_FLAG_SAFETY_ARMED) > 0
        if armed != self.armed:
            self.armed = armed
            if armed:
                print("ARMED")
                print(airmap.pilot['id'])
                flightplan = AirmapFlightplan()
                latitude = 52.168014
                longitude = 4.412414
                flightplan.takeoff_latitude = str(latitude)
                flightplan.takeoff_longitude = str(longitude)

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
                telem.start(airmap.flight['flight_id'], airmap.comm['key'])
                print("[airmap] flight submitted")

            else:
                print("DISARMED")
                # register flight end with airmap
                airmap.end_comm()
                airmap.end_flight()
                print("[airmap] flight ended")

    def set_state(self, new_state):
        self.state = new_state

vehicle = Vehicle()

async def pingloop():
    while (True):
        mav.mav.heartbeat_send(18, 0, 0, 0, 4)
        if vehicle.armed:
                    telem.send_update()
        await asyncio.sleep(0.2)

async def handle_arm_request():
    mav.mav.command_ack_send(3001, 5, 0, 0, 1, 0)
    print("Send airmap request here")
    # await asyncio.sleep(4)
    mav.mav.command_ack_send(3001, 0, 0, 0, 1, 0)
    print("Airmap request approved")

async def receive():
    while True:
        msg = mav.recv_match(type=['COMMAND_LONG','SYS_STATUS','HEARTBEAT', 'GLOBAL_POSITION_INT'])
        if msg != None:
            if msg.name == 'COMMAND_LONG' and msg.command == 3001:
                loop.create_task(handle_arm_request())
            elif msg.name == 'SYS_STATUS':
                pass
                #print(msg)
            elif msg.name == 'HEARTBEAT' and msg.autopilot == mavlink.MAV_AUTOPILOT_PX4:
                print(msg)
                vehicle.parse_heartbeat(msg)
            elif msg.name == 'GLOBAL_POSITION_INT':
                #print(msg)
                telem.update_position(msg.lat * 1e-7, msg.lon * 1e-7, msg.relative_alt*1e-3, msg.alt*1e-3, 10.0)
        await asyncio.sleep(0.1)

async def main():
    airmap.login()
    airmap.get_pilot()

    tasks = []
    tasks.append(loop.create_task(pingloop()))
    tasks.append(loop.create_task(receive()))
    
    # a clean way to exit
    loop.add_signal_handler(getattr(signal, 'SIGINT'), clean_exit)
    await asyncio.wait(tasks)

def clean_exit():
    print("Stop the event loop")
    loop.stop()
    print("Remove airmap connections")
    if airmap.comm != None:
        print("[airmap] end comm")
        airmap.end_comm()
    if airmap.flight['flight_id'] != None:
        print("[airmap] end flight")
        airmap.end_flight()

if __name__ == "__main__":
    #print("name == main")
    loop.run_until_complete(main())
