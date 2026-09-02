from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="MetroFlow API",
    description="AI Predictive Public Transit Intelligence Platform",
    version="1.0.0"
)


# Login request model
class LoginRequest(BaseModel):
    email: str
    password: str
    role: str


@app.get("/")
def home():
    return {
        "message": "Welcome to MetroFlow API",
        "status": "Backend is running"
    }


# Login API
@app.post("/login")
def login(user: LoginRequest):

    # Temporary demo authentication
    if user.email == "admin@metroflow.com" and user.password == "admin123":
        return {
            "success": True,
            "message": "Login successful",
            "role": user.role
        }

    return {
        "success": False,
        "message": "Invalid email or password"
    }