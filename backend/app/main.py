from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.db.base import Base
from app.db.session import engine
from app.workers.scheduler import start_scheduler

app = FastAPI(title='ReimagineDoomscrolling API')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])


@app.on_event('startup')
def startup():
    Base.metadata.create_all(bind=engine)
    start_scheduler()


app.include_router(router, prefix='/api')
