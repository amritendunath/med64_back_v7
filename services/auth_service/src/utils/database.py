from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os
import logging

logger = logging.getLogger(__name__)
load_dotenv()


class Database:
    def __init__(self):
        self.client = MongoClient(
            os.getenv("MONGODBURI"), server_api=ServerApi("1")
        )  # Use ServerApi for compatibility
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

        # Dictionary to store email to user_ehr_id mapping
        self.email_to_user_ehr_id = {}
        self.user_ehr_id_to_email = {}

    def insert_user(self, user_data):
        result = self.users.insert_one(user_data)
        return result
        # user_ehr_id = result.inserted_id
        # email = user_data.get('email')
        # if email and user_ehr_id:
        #     self.email_to_user_ehr_id[email] = user_ehr_id
        #     self.user_ehr_id_to_email[user_ehr_id] = email
        # return result

    def get_user_ehr_id_by_email(self, email):
        return self.email_to_user_ehr_id.get(email)

    def get_email_by_user_ehr_id(self, user_ehr_id):
        return self.user_ehr_id_to_email.get(user_ehr_id)

    def fetch_user_by_email(self, email):
        user = self.users.find_one({"email": email})
        if user:
            user_ehr_id = user.get("_id")
            self.email_to_user_ehr_id[email] = user_ehr_id
            self.user_ehr_id_to_email[user_ehr_id] = email
        return user

    def fetch_user_by_user_ehr_id(self, user_ehr_id):
        user = self.users.find_one({"_id": user_ehr_id})
        if user:
            email = user.get("email")
            self.email_to_user_ehr_id[email] = user_ehr_id
            self.user_ehr_id_to_email[user_ehr_id] = email
        return user


# from pymongo.mongo_client import MongoClient
# from pymongo.server_api import ServerApi
# from dotenv import load_dotenv
# import os

# load_dotenv()

# uri = "mongodb+srv://amritendunath1:mcZIh40RvT5ATcaX@cluster0.funclfu.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# # Create a new client and connect to the server
# client = MongoClient(uri)

# # Send a ping to confirm a successful connection
# try:
#     client.admin.command('ping')
#     print("Pinged your deployment. You successfully connected to MongoDB!")
# except Exception as e:
#     print("MongoDB connection failed:", e)

# class Database:

#     def __init__(self):
#         # self.client = MongoClient(os.getenv('MONGODB_URI'))
#         # self.client = MongoClient(os.getenv('MONGODB_URI'), server_api=ServerApi('1'))  # Use ServerApi for compatibility
#         self.client = MongoClient(uri, server_api=ServerApi('1'))  # Use ServerApi for compatibility
#         # self.client = MongoClient(os.getenv('MONGODB_URI'))
#         self.db = self.client['sathi_chatbot']  # Different database name for sathi

#         # Collections
#         self.users = self.db['users']
#         self.chats = self.db['chats']
#         self.appointments = self.db['appointments']
#         self.medical_records = self.db['medical_records']
#         self.sessions = self.db['sessions']

#         # Create indexes
#         self.users.create_index('email', unique=True)
#         self.chats.create_index([('user_email', 1), ('timestamp', -1)])
#         self.chats.create_index('session_id')
#         self.appointments.create_index([('user_email', 1), ('appointment_date', 1)])
#         self.medical_records.create_index('user_email', unique=True)
#         self.sessions.create_index([('user_email', 1), ('end_time', 1)])
#         self.sessions.create_index('session_id', unique=True)


#         # Dictionary to store email to user_ehr_id mapping
#         self.email_to_user_ehr_id = {}
#         self.user_ehr_id_to_email = {}

#     def insert_user(self, user_data):
#         result = self.users.insert_one(user_data)
#         user_ehr_id = result.inserted_id
#         email = user_data.get('email')
#         if email and user_ehr_id:
#             self.email_to_user_ehr_id[email] = user_ehr_id
#             self.user_ehr_id_to_email[user_ehr_id] = email
#         return result

#     def get_user_ehr_id_by_email(self, email):
#         return self.email_to_user_ehr_id.get(email)

#     def get_email_by_user_ehr_id(self, user_ehr_id):
#         return self.user_ehr_id_to_email.get(user_ehr_id)

#     def fetch_user_by_email(self, email):
#         user = self.users.find_one({'email': email})
#         if user:
#             user_ehr_id = user.get('_id')
#             self.email_to_user_ehr_id[email] = user_ehr_id
#             self.user_ehr_id_to_email[user_ehr_id] = email
#         return user

#     def fetch_user_by_user_ehr_id(self, user_ehr_id):
#         user = self.users.find_one({'_id': user_ehr_id})
#         if user:
#             email = user.get('email')
#             self.email_to_user_ehr_id[email] = user_ehr_id
#             self.user_ehr_id_to_email[user_ehr_id] = email
#         return user

# db = Database()
