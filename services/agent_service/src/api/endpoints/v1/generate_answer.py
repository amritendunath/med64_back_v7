from fastapi import APIRouter, Depends, HTTPException, status
from models.generate_answer import GenerationResponse, GenerationRequest, ErrorResponse
from fastapi.responses import JSONResponse, StreamingResponse
from langchain_core.messages import HumanMessage
from fastapi import FastAPI, HTTPException, Header, Query
from agents.builder import build_graph
import logging
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import os, uuid
from datetime import datetime
from utils.database import db
from langchain_core.runnables import RunnableConfig

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI


import asyncio
import redis.asyncio as redis  # Use redis.asyncio

from fastapi import FastAPI
import contextvars

from agents.agent_chain import create_agent_chain


app = FastAPI()
# r = redis.Redis()  # Initialize async Redis client

r = None
redis_connected = False
try:
    r = redis.Redis()
    r.ping()
    redis_connected = True
    if redis_connected:
        pubsub = r.pubsub()
        pubsub.subscribe("chat_queue")
except Exception as e:
    logging.error(f"Redis connection failed: {e}")
    redis_connected = False

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY not set in environment")

ALGORITHM = "HS256"

graph = build_graph()
logging.info("Loaded graph")

ehr_id_var = contextvars.ContextVar("ehr_id")

async def get_current_user_id(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # email: str = payload.get("sub")
        ehr_id: str = payload.get("user_ehr_id")
        # if ehr_id is None or email is None:
        if ehr_id is None:
            raise credentials_exception
        return ehr_id
    except JWTError:
        raise credentials_exception

async def get_user_from_token(token: str =Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        ehr_id: str = payload.get("user_ehr_id")
        if ehr_id is None or email is None:
            raise credentials_exception
        return {'email': email, 'user_id': ehr_id}
    except JWTError:
        raise credentials_exception


async def create_new_session(user_email: str):
    try:
        # Create new session
        session_id = str(uuid.uuid4())
        db.sessions.insert_one({
            "user_email": user_email,
            "session_id": session_id,
            "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": None,
        })

        logger.info(f"New session created with ID: {session_id}")
        return session_id
    except Exception as e:
        logger.error(f"Failed to create new session: {str(e)}")
        raise


llm = ChatGoogleGenerativeAI(
    model='gemini-2.0-flash-lite',
    google_api_key='AIzaSyCP99HXunPMPTWkitdFEzGBFgAXp62mYbg',
    temperature=0,
    convert_system_message_to_human=True,
)
prompt = ChatPromptTemplate.from_template(
    """Generate a small name based on the following query of max 30 letters or 4 words: {query}
    - Don't use any special character
    """
)
chain = prompt | llm | StrOutputParser()


async def generate_session_title(query: str) -> str:
    """Generate a session title using the LLM."""
    return await chain.ainvoke({"query": query})



async def your_api_endpoint_function(current_user: str, session_id: str, query: str, messages: str):
    # Check if this is the first query in the session
    first_query = not db.chats.find_one({"user_email": current_user, "session_id": session_id})

    if first_query:
        session_title = await generate_session_title(query)
    else:
        session_title = db.chats.find_one({"user_email": current_user, "session_id": session_id})["session_title"]

    chat_document = {
        "user_email": current_user,
        "session_id": session_id,
        "message": query,
        "response": messages,
        "timestamp": datetime.utcnow(),
        "session_title": session_title
    }
    db.chats.insert_one(chat_document)
# async def connection():
#     r = None
#     redis_connected = False
#     try:
#         r = redis.Redis()
#         await r.ping()
#         redis_connected = True
#         if redis_connected:
#             pubsub = r.pubsub()
#             await pubsub.subscribe("chat_queue")
#     except Exception as e:
#         logging.error(f"Redis connection failed: {e}")
#         redis_connected = False


@app.on_event("startup")
async def startup():
    asyncio.create_task(generation_streaming())


@router.post(
    "/generate-stream/",
    response_model=GenerationResponse,
    responses={500: {
        "model": ErrorResponse
    }},
)
async def generation_streaming(
        request: GenerationRequest,
        thread_id: str = Header("111222", alias="X-THREAD-ID"),
        current_user: str = Depends(get_current_user_id),
        user: dict = Depends(get_user_from_token),
        token: str = Depends(oauth2_scheme),
):
    query = request.query
    queryModeType = request.queryModeType
    logging.info(
        f"Received the Query - {query} & thread_id - {thread_id} and Type: {queryModeType}"
    )
    ehr_id_var.set(current_user)
    # 134 - 146: Websocket
    # r = None
    # redis_connected = False
    # try:
    #     r = redis.Redis()
    #     await r.ping()
    #     redis_connected = True
    #     if redis_connected:
    #         pubsub = r.pubsub()
    #         await pubsub.subscribe("chat_queue")
    # except Exception as e:
    #     logging.error(f"Redis connection failed: {e}")
    #     redis_connected = False

    try:
        # Decode the token to get user information
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email: str = payload.get("sub")
        ehr_id: str = payload.get("user_ehr_id")
        # user_email, ehr_id = current_user
        # Check for any existing active sessions for this user
        existing_session = db.sessions.find_one({
            "user_email": current_user,
            "end_time": None
        })

        # If no active session exists, create a new one
        if not existing_session:
            session_id = str(uuid.uuid4())
            db.sessions.insert_one({
                "user_email": current_user,
                "session_id":session_id,
                "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": None
            })
            logger.info(
                f"Created new session {session_id} for user {current_user}")
        else:
            session_id = existing_session["session_id"]
            logger.info(
                f"Using existing session {session_id} for user {current_user}")

        # Process the chat message

        inputs = [HumanMessage(content=query)]
        state = {"messages": inputs, "mode": queryModeType}
        config = RunnableConfig(
            configurable={
                "thread_id": thread_id,
                "recursion_limit": 10,
                "user_email": user_email,
                "current_user": current_user
            })
        # response = graph.invoke(input=state)
        if queryModeType == 'quick':
            response = graph.invoke(input=state, config=config)
            logging.info("Generated Answer from Graph")
            dialog_states = response["dialog_state"]
            dialog_state = dialog_states[
                -1] if dialog_states else "primary_assistant"
            messages = response["messages"][-1].content

        elif queryModeType == 'think':
            agent = create_agent_chain(user['user_id'], user['email'] )
            response = agent.invoke({"messages": request.query})
            messages = response
            dialog_state = None

        # logging.info("Generated Answer from Graph")
        # dialog_states = response["dialog_state"]
        # dialog_state = dialog_states[
        #     -1] if dialog_states else "primary_assistant"
        # messages = response["messages"][-1].content


        # generate_session_title(query)
        await your_api_endpoint_function(current_user, session_id, query, messages)


        # response_data = {
        #     "dialog_state": dialog_state if dialog_state else "",
        #     "answer": messages if messages else "",
        #     "session_id": session_id,
        # }

        if "booked" in messages:
            db.appointments.update_one(
                {
                    "status": "booked",
                    "user_email": {
                        "$exists": False
                    }
                },
                {
                    "$set": {
                        "user_email": current_user,
                        "session_id": session_id
                    }
                },
            )

        # 235 - 247: websocket
        # if r and redis_connected:
        #     await r.publish("chat_response", json.dumps(response_data))
        # else:
        #     return JSONResponse({
        #         "dialog_state": dialog_state if dialog_state else "",
        #         "answer": messages if messages else "",
        #         "session_id": session_id,
        #     })
        # try:
        #     if r and redis_connected:
        #         await r.publish("chat_response", json.dumps(response_data))
        # except Exception as e:
        return JSONResponse({
            "dialog_state": dialog_state if dialog_state else "",
            "answer": messages if messages else "",
            "session_id": session_id,
        })

    except Exception as e:
        logger.error(f"Error in chat processing: {str(e)}")
        raise HTTPException(status_code=500,
                            detail=f"Failed to process chat: {str(e)}")


@router.post("/generate-stream/end-session")
async def end_session(current_user: str = Depends(get_current_user_id)):
    try:
        # Find the active session for the user
        active_session = db.sessions.find_one({
            "user_email": current_user,
            "end_time": None
        })

        if active_session:
            # Update the session end time
            db.sessions.update_one(
                {"_id": active_session["_id"]},
                {
                    "$set": {
                        "end_time":
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                },
            )
        return JSONResponse({
            "message": "Session ended successfully",
            "session_id": active_session["session_id"],
        })

    except Exception as e:
        logger.error(f"Error ending session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/generate-stream/appointment/", include_in_schema=True)
async def get_user_appointments(
        current_user: str = Depends(get_current_user_id)):
    try:
        query = {"user_email": current_user}
        appointments = list(db.appointments.find(query, {"_id": 0}))

        # Format the appointments to ensure proper date handling
        formatted_appointments = []
        for appointment in appointments:
            formatted_appointment = {
                "doctor_name": appointment.get("doctor_name", ""),
                "appointment_date": appointment.get("appointment_date", ""),
                "status": appointment.get("status", ""),
                "user_email": appointment.get("user_email", ""),
                "session_id": appointment.get("session_id", ""),
            }
            formatted_appointments.append(formatted_appointment)

        # Log the appointments for debugging
        logger.info(
            f"Fetched appointments for user {current_user}: {formatted_appointments}"
        )

        return JSONResponse({"appointments": formatted_appointments})
    except Exception as e:
        logger.error(f"Error fetching appointments: {str(e)}")
        raise HTTPException(status_code=500,
                            detail=f"Failed to fetch appointments: {str(e)}")


@router.get("/generate-stream/chat-history/{session_id}")
async def get_chat_history(session_id: str,
                           current_user: str = Depends(get_current_user_id)):
    try:
        pipeline = [
            {
                "$match": {
                    "user_email": current_user,
                    "session_id": session_id
                }
            },
            {
                "$sort": {
                    "timestamp": 1
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "message": 1,
                    "response": 1,
                    "timestamp": 1,
                    "type": 1,
                    "tag": 1,
                }
            },
        ]

        chat_history = list(db.chats.aggregate(pipeline))

        formatted_history = []
        for chat in chat_history:
            # Convert datetime to ISO format string for JSON serialization
            timestamp = (chat["timestamp"].isoformat() if isinstance(
                chat["timestamp"], datetime) else chat["timestamp"])

            formatted_history.append({
                "message": chat["message"],
                "type": "user",
                "timestamp": timestamp
            })
            formatted_history.append({
                "message": chat["response"],
                "type": "bot",
                "timestamp": timestamp
            })

        return JSONResponse(content={"chat_history": formatted_history})
    except Exception as e:
        logger.error(f"Error fetching chat history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/generate-stream/chat-sessions")
async def get_chat_sessions(current_user: str = Depends(get_current_user_id)):
    try:
        user_email = current_user

        # Fetch distinct chat sessions for the user
        pipeline = [
            {
                "$match": {
                    "user_email": user_email
                }
            },
            {
                "$group": {
                    "_id": "$session_id",
                    "title": {
                        "$first": "$session_title"
                    },
                    "timestamp": {
                        "$first": "$timestamp"
                    },
                }
            },
            {
                "$sort": {
                    "timestamp": -1
                }
            },
        ]

        sessions = list(db.chats.aggregate(pipeline))

        # Format the sessions to ensure proper date handling
        formatted_sessions = []
        for session in sessions:
            formatted_session = {
                "session_id": session["_id"],
                "title": session.get("title", "Untitled Chat"),
                "timestamp": (session["timestamp"].isoformat() if isinstance(
                    session["timestamp"], datetime) else session["timestamp"]),
            }
            formatted_sessions.append(formatted_session)

        return JSONResponse(content={"sessions": formatted_sessions})
    except Exception as e:
        logger.error(f"Error fetching chat sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
