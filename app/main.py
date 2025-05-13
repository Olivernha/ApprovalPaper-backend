from fastapi import FastAPI

from app.database.DBconnection import MongoDB

async def lifespan(app: FastAPI):
    """Lifespan event for the application"""
    print("Connecting to MongoDB...")
    await MongoDB.connect_to_database()
    print("Connected to MongoDB.")
    yield

app = FastAPI(lifespan=lifespan)


from app.routes import userRoute
app.include_router(userRoute.router)