import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.server_api import ServerApi

load_dotenv()

uri = os.environ["MONGODB_URI"]
client = MongoClient(uri, server_api=ServerApi("1"))
client.admin.command("ping")
print("OK: connected to MongoDB Atlas")
print("Databases:", client.list_database_names())
