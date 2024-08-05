import websockets
import json
from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


app = FastAPI()
templates = Jinja2Templates(directory="templates")

BINANCE_WS_URL = "wss://stream.binance.com:9443/ws/"
KRAKEN_WS_URL = "wss://ws.kraken.com/"


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    context = {"request": request}

    return templates.get_template("index.html").render(context)


@app.websocket("/ws/binance")
async def ws_binance_endpoint(websocket: WebSocket):
    await websocket.accept()

    while True:
        data = await websocket.receive_text()
        params = json.loads(data)
        pair = params.get("pair")
        uri = f"{BINANCE_WS_URL}{''.join(pair.split('/')).lower()}@trade"

        async with websockets.connect(uri) as b_websocket:
            while True:
                data = await b_websocket.recv()
                data = json.loads(data)

                await websocket.send_text(f"{pair}: {data['p']}")


@app.websocket("/ws/kraken")
async def ws_kraken_endpoint(websocket: WebSocket):
    await websocket.accept()

    while True:
        data = await websocket.receive_text()
        params = json.loads(data)
        pair = params.get("pair")
        subscribe_message = {
            "event": "subscribe",
            "subscription": {"name": "ticker"},
            "pair": [pair.upper()]
        }

        async with websockets.connect(KRAKEN_WS_URL) as k_websocket:
            await k_websocket.send(json.dumps(subscribe_message))

            while True:
                data = await k_websocket.recv()
                data = json.loads(data)

                if isinstance(data, list):
                    message = data[1]
                    bid = float(message.get('a')[0])
                    ask = float(message.get('b')[0])
                    price = (bid + ask) / 2

                    await websocket.send_text(f"{pair}: {price}")
