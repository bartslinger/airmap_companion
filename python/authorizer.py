#!/usr/bin/env python3

import asyncio

import pymavlink.mavutil as mavutil
import pymavlink.dialects.v20.common as mavlink
import sys
import time

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
            else:
                print("DISARMED")
                # register flight end with airmap

    def set_state(self, new_state):
        self.state = new_state

vehicle = Vehicle()

async def pingloop():
    while (True):
        mav.mav.heartbeat_send(18, 0, 0, 0, 4)
        await asyncio.sleep(1.00)

async def handle_arm_request():
    mav.mav.command_ack_send(3001, 5, 0, 0, 1, 0)
    print("Send airmap request here")
    await asyncio.sleep(4)
    mav.mav.command_ack_send(3001, 0, 0, 0, 1, 0)
    print("Airmap request approved")

async def receive_command_long():
    global arming_requested
    while True:
        msg = mav.recv_match(type=['COMMAND_LONG','SYS_STATUS','HEARTBEAT'])
        if msg != None:
            if msg.name == 'COMMAND_LONG' and msg.command == 3001:
                loop.create_task(handle_arm_request())
            elif msg.name == 'SYS_STATUS':
                pass
                #print(msg)
            elif msg.name == 'HEARTBEAT':
                vehicle.parse_heartbeat(msg)
        await asyncio.sleep(0.1)

async def main():
    tasks = []
    tasks.append(loop.create_task(pingloop()))
    tasks.append(loop.create_task(receive_command_long()))
    await asyncio.wait(tasks)

if __name__ == "__main__":
    #print("name == main")
    loop.run_until_complete(main())
