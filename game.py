import asyncio
import json
import logging
import websockets
import uuid
import random
import math
logging.basicConfig()

USERS = []
HIGHSCORES = {}
NAMES = {}

def users_event():
    return json.dumps({'type': 'users', 'count': len(USERS)})

async def notify_users():
    if USERS:       # asyncio.wait doesn't accept an empty list
        message = users_event()
        await asyncio.wait([user.send(message) for user in USERS])

def update_scores():
    scores = ""
    for key in HIGHSCORES:
        scores = scores + str(key) + ": " + str(HIGHSCORES[key]) + "<br>"
    return json.dumps({'type': 'score', 'highscore': scores})

async def notify_highscores():
    if USERS:       # asyncio.wait doesn't accept an empty list
        scores = update_scores()
        await asyncio.wait([user.send(scores) for user in USERS])

async def register(websocket):
    USERS.append(websocket)
    print("User Connected: " + str(websocket))
    await notify_users()

async def unregister(websocket):
    USERS.remove(websocket)
    print("User Disconnected: " + str(websocket))
    await notify_users()

async def update(websocket, path):
    # register(websocket) sends user_event() to websocket
    await register(websocket)
    try:
        async for message in websocket:
            data = json.loads(message)
            if data['action'] == 'highscore':
                key = data['name']
                score = data['score']
                if key in HIGHSCORES:
                    if HIGHSCORES[key] < score:
                        HIGHSCORES[key] = round(score)
                else:
                    HIGHSCORES[key] = round(score)
                await notify_highscores()
            else:
                print("Error")
    finally:
        await unregister(websocket)

asyncio.get_event_loop().run_until_complete(
    websockets.serve(update, '172.22.3.133', 6789))
asyncio.get_event_loop().run_forever()