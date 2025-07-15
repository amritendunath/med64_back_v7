from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os

load_dotenv()


class Database:
    def __init__(self):
        self.client = MongoClient(os.getenv('MONGODB_URI'))
        self.client.admin.command("Ping")
        # self.client = MongoClient(os.getenv('MONGODB_URI'), server_api=ServerApi('1'))  # Use ServerApi for compatibility
        # self.client = MongoClient(
        #     uri, server_api=ServerApi("1")
        # )
        # self.client = MongoClient(os.getenv('MONGODB_URI'))
        self.db = self.client["sathi_chatbot"]  # Different database name for sathi

        # Collections
        self.users = self.db["users"]
        self.chats = self.db["chats"]
        self.appointments = self.db["appointments"]
        self.medical_records = self.db["medical_records"]
        self.sessions = self.db["sessions"]

        # Create indexes
        self.users.create_index("email", unique=True)
        self.chats.create_index([("user_email", 1), ("timestamp", -1)])
        self.chats.create_index("session_id")
        self.appointments.create_index([("user_email", 1), ("appointment_date", 1)])
        self.medical_records.create_index("user_email", unique=True)
        self.sessions.create_index([("user_email", 1), ("end_time", 1)])
        self.sessions.create_index("session_id", unique=True)


db = Database()
