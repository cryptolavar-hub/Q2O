import json
import logging
from typing import List, Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from pydantic import BaseModel, constr, conlist
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Pydantic models
class User(BaseModel):
    username: constr(min_length=3, max_length=50)
    email: constr(regex=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    full_name: str
    disabled: bool = False

class Group(BaseModel):
    name: constr(min_length=1, max_length=100)
    members: conlist(str, min_items=1)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str

# Fake database for demonstration
fake_users_db: Dict[str, User] = {}
fake_groups_db: Dict[str, Group] = {}

# FastAPI app
app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Utility functions
def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = fake_users_db.get(token_data.username)
    if user is None:
        raise credentials_exception
    return user

# WebSocket handling
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, group_name: str):
        await websocket.accept()
        self.active_connections[group_name] = websocket
        logger.info(f"Client connected to group: {group_name}")

    def disconnect(self, websocket: WebSocket, group_name: str):
        del self.active_connections[group_name]
        logger.info(f"Client disconnected from group: {group_name}")

    async def send_message(self, message: str, group_name: str):
        if group_name in self.active_connections:
            websocket = self.active_connections[group_name]
            await websocket.send_text(message)

manager = ConnectionManager()

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = fake_users_db.get(form_data.username)
    if not user or not user.disabled:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.websocket("/ws/{group_name}")
async def websocket_endpoint(websocket: WebSocket, group_name: str, current_user: User = Depends(get_current_user)):
    await manager.connect(websocket, group_name)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_message(f"{current_user.username}: {data}", group_name)
    except WebSocketDisconnect:
        manager.disconnect(websocket, group_name)

@app.post("/groups/", response_model=Group)
async def create_group(group: Group):
    if group.name in fake_groups_db:
        raise HTTPException(status_code=400, detail="Group already exists")
    fake_groups_db[group.name] = group
    return group

@app.get("/groups/{group_name}", response_model=Group)
async def read_group(group_name: str):
    if group_name not in fake_groups_db:
        raise HTTPException(status_code=404, detail="Group not found")
    return fake_groups_db[group_name]