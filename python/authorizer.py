#!/usr/bin/env python3

import asyncio

import pymavlink.mavutil as mavutil
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
        msg = mav.recv_match(type="COMMAND_LONG")
        if msg != None:
            if msg.command == 3001:
                loop.create_task(handle_arm_request())
        await asyncio.sleep(0.1)

async def main():
    tasks = []
    tasks.append(loop.create_task(pingloop()))
    tasks.append(loop.create_task(receive_command_long()))
    await asyncio.wait(tasks)

if __name__ == "__main__":
    #print("name == main")
    loop.run_until_complete(main())
