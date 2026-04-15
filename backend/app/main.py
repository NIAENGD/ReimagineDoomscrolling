import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.db.base import Base
from app.db.session import engine
from app.workers.scheduler import start_scheduler

app = FastAPI(title='ReimagineDoomscrolling API')

# By default, allow localhost and any IPv4-address origins so frontend dev servers
# running on other machines in the same network can call this backend.
def _parse_cors_origins():
    raw = os.getenv(
        'CORS_ORIGINS',
        'http://localhost:5173,http://127.0.0.1:5173,https://readeros.duckdns.org,http://readeros.duckdns.org',
    )
    return [origin.strip() for origin in raw.split(',') if origin.strip()]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_parse_cors_origins(),
    allow_origin_regex=r"^https?://((localhost)|(127\.0\.0\.1)|((\d{1,3}\.){3}\d{1,3}))(:\d+)?$",
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.on_event('startup')
def startup():
    Base.metadata.create_all(bind=engine)
    start_scheduler()


@app.get('/')
def root():
    return {'status': 'ok', 'api': '/api'}


@app.get('/health')
def health():
    return {'status': 'ok'}


app.include_router(router, prefix='/api')
