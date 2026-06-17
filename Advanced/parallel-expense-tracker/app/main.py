from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app.routes import router

app = FastAPI(title="Expense Tracker")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


# Register the API router BEFORE mounting static files so that /api/* is
# handled by the router and not swallowed by the static mount at "/".
app.include_router(router)

app.mount("/", StaticFiles(directory="static", html=True), name="static")
