import asyncio
import json
import logging
import websockets

logging.basicConfig()

STATE = {'value': 0}
CHAT = {'chat': ""}
USERS = set()
USERNAMES = dict()
def state_event():
    return json.dumps({'type': 'state', **STATE})

def users_event():
    return json.dumps({'type': 'users', 'count': len(USERS)})

def chat_event():
    return json.dumps({'type': 'msg', **CHAT})

async def notify_state():
    if USERS:       # asyncio.wait doesn't accept an empty list
        message = state_event()
        await asyncio.wait([user.send(message) for user in USERS])

async def notify_users():
    if USERS:       # asyncio.wait doesn't accept an empty list
        message = users_event()
        await asyncio.wait([user.send(message) for user in USERS])

async def notify_chat():
    if USERS:       # asyncio.wait doesn't accept an empty list
        message = chat_event()
        
        await asyncio.wait([user.send(message) for user in USERS])

async def register(websocket):
    USERS.add(websocket)
    await notify_users()

async def unregister(websocket):
    USERS.remove(websocket)
    await notify_users()

async def counter(websocket, path):
    # register(websocket) sends user_event() to websocket
    await register(websocket)
    try:
        await websocket.send(state_event())
        async for message in websocket:
            data = json.loads(message)
            if data['action'] == 'minus':
                STATE['value'] -= 1
                await notify_state()
            elif data['action'] == 'plus':
                STATE['value'] += 1
                await notify_state()
            elif data['action'] == 'login':
                USERNAMES.update({websocket: data['user']})
            elif data['action'] == 'chat':
                CHAT['chat'] += USERNAMES[websocket] + ": " +  data['msg'] + "<br>"
                await notify_chat()
            else:
                logging.error(
                    "unsupported event: {}", data)
    finally:
        await unregister(websocket)

asyncio.get_event_loop().run_until_complete(
    websockets.serve(counter, '172.22.3.133', 6789))
asyncio.get_event_loop().run_forever()