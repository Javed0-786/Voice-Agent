import os
import random
from aiohttp import web
from dotenv import load_dotenv
from livekit import api
import database

load_dotenv()

LIVEKIT_URL = os.getenv("LIVEKIT_URL", "ws://127.0.0.1:7880")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "devkey")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "secret")
PORT = int(os.getenv("WEB_PORT", 3000))

async def handle_token(request: web.Request) -> web.Response:
    room = request.query.get("room", "aura-room")
    identity = request.query.get("identity", f"client-{random.randint(1000, 9999)}")
    name = request.query.get("name", "Caller")

    token = (
        api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        .with_identity(identity)
        .with_name(name)
        .with_grants(api.VideoGrants(room_join=True, room=room))
        .to_jwt()
    )

    return web.json_response({
        "token": token,
        "url": LIVEKIT_URL,
        "room": room,
        "identity": identity
    })

async def handle_get_bookings(request: web.Request) -> web.Response:
    bookings = database.get_all_bookings()
    return web.json_response({"bookings": bookings})

async def handle_get_services(request: web.Request) -> web.Response:
    services = database.get_services()
    return web.json_response({"services": services})

def create_app() -> web.Application:
    app = web.Application()
    
    # API endpoints
    app.router.add_get("/api/token", handle_token)
    app.router.add_get("/api/bookings", handle_get_bookings)
    app.router.add_get("/api/services", handle_get_services)

    # Static Web UI
    web_dir = os.path.join(os.path.dirname(__file__), "web")
    if not os.path.exists(web_dir):
        os.makedirs(web_dir, exist_ok=True)
    
    app.router.add_static("/", path=web_dir, show_index=True)
    return app

if __name__ == "__main__":
    app = create_app()
    print("==================================================")
    print(" [Aura Clinic] Web Dashboard & Token Service")
    print(f" URL:            http://localhost:{PORT}")
    print(f" LiveKit URL:    {LIVEKIT_URL}")
    print("==================================================")
    web.run_app(app, host="0.0.0.0", port=PORT)
