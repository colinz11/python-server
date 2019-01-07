import asyncio
import json
import logging
import websockets
import uuid
import random
import math
logging.basicConfig()

USERS = []
PLAYERS = {}
NAMES = {}

def check_players(websocket):
    for key in PLAYERS:
        other = PLAYERS[key]
        player = PLAYERS[str(websocket)]
        if player != other:
            otherPos = [x.strip() for x in other.split(',')]
            playerPos = [x.strip() for x in player.split(',')]
            d = math.pow(math.pow(float(playerPos[0]) - float(otherPos[0]),2) + math.pow(float(playerPos[1]) - float(otherPos[1]),2),0.5)
            if d < float(playerPos[2]) + float(otherPos[2]):
                sum = math.pi * math.pow(float(playerPos[2]),2) + math.pi * math.pow(float(otherPos[2]),2) 
                if float(playerPos[2]) > float(otherPos[2]):
                    PLAYERS[str(websocket)] = playerPos[0] + "," + playerPos[1] + "," + str(math.pow((sum / math.pi),0.5)) 
                    return key
                elif float(playerPos[2]) < float(otherPos[2]):
                    #PLAYERS[key] = otherPos[0] + "," + otherPos[1] + "," + str(math.pow((sum / math.pi),0.5))
                    return str(websocket) 
                else:
                    print("equal")

def users_event():
    return json.dumps({'type': 'users', 'count': len(USERS)})

def update_players(websocket):
    key = check_players(websocket)
    PLAYERS.pop(key, None)
    playerpos = []
    for key in PLAYERS:
        playerpos.append(PLAYERS[key])
    return json.dumps({'type': 'update', 'players': playerpos})

def get_position():
    return json.dumps({'type': 'pos', 'pos': str(random.randint(-600,600)) + "," + str(random.randint(-600,600))})

def get_id():
    return json.dumps({'type': 'id', 'id': str(uuid.uuid4())})

async def notify_users():
    if USERS:       # asyncio.wait doesn't accept an empty list
        message = users_event()
        await asyncio.wait([user.send(message) for user in USERS])

async def notify_pos(websocket):
    if USERS:       # asyncio.wait doesn't accept an empty list
        pos = get_position()
        await asyncio.wait([websocket.send(pos)])

async def notify_id(websocket):
    if USERS:       # asyncio.wait doesn't accept an empty list
        id = get_id()
        await asyncio.wait([websocket.send(id)])

async def update_map(websocket):
    if USERS:
        update = update_players(websocket)
        await asyncio.wait([user.send(update) for user in USERS])

async def register(websocket):
    USERS.append(websocket)
    print("User Connected: " + str(websocket))
    await notify_pos(websocket)
    await notify_id(websocket)
    await notify_users()

async def unregister(websocket):
    if str(websocket) in PLAYERS:
        del PLAYERS[str(websocket)]
    USERS.remove(websocket)
    print("User Disconnected: " + str(websocket))
    await notify_users()

async def update(websocket, path):
    # register(websocket) sends user_event() to websocket
    await register(websocket)
    try:
        async for message in websocket:
            data = json.loads(message)
            if data['action'] == 'update':
                PLAYERS[str(websocket)] = str(data['posX']) + "," + str(data['posY']) + "," + str(data['radius'])
                await update_map(websocket)              
            else:
                logging.error("unsupported event: {}", data)
    finally:
        await unregister(websocket)

asyncio.get_event_loop().run_until_complete(
    websockets.serve(update, '172.22.3.133', 6789))
asyncio.get_event_loop().run_forever()