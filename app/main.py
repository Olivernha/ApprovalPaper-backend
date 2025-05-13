from fastapi import FastAPI

from app.database.DBconnection import MongoDB

async def lifespan(app: FastAPI):
    """Lifespan event for the application"""
    print("Connecting to MongoDB...")
    await MongoDB.connect_to_database()
    print("Connected to MongoDB.")
    yield

app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Welcome to the Approval Paper API!"}