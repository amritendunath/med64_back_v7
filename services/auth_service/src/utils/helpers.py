import redis
import logging
import random
import string
import hashlib
# from flask import session
from dotenv import load_dotenv
import os

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get Redis connection parameters from environment variables
redis_host = os.environ.get("REDIS_HOST")
redis_port = os.environ.get("REDIS_PORT")
redis_db = os.environ.get("REDIS_DB")

# Create a Redis client instance
r = redis.Redis(
    host=redis_host,
    port=redis_port,
    db=redis_db,
)


class RouteUpdater:

    def __init__(self, r = r, logger = logger):
        """
        Initialize the service with a Redis connection and a logger.

        Args:
            r (redis.Redis): Redis client instance.
            logger (logging.Logger): Logger instance.
        """
        self.r = r
        self.test = self.r.ping()
        self.logger = logger



    # def generate_state_token(self) -> str:
    #     """
    #     Generate a secure random state token using SHA-256 hashing.

    #     Returns:
    #         str: A securely generated state token as a hexadecimal string.
    #     """
    #     state_token = hashlib.sha256(os.urandom(1024)).hexdigest()
    #     session['oauth_state'] = state_token
    #     return state_token



    def get_next_ehr_id(self)-> str:
        """
        Retrieve the next EHR ID by incrementing a counter in the cache 
        and return it as a zero-padded string.

        Returns:
            str: The next EHR ID as a zero-padded 7-digit string.
        """
        new_id = self.r.incr("ehr_id_counter")
        return str(new_id).zfill(7)



    def generate_verification_code(self) -> str:
        """
        Generate a random 6-digit verification code.

        Returns:
            str: A randomly generated 6-digit verification code.
        """
        return "".join(random.choices(string.digits, k=6))
    


    def store_verification_code(self, key: str) -> dict:
        """
        Store a verification code in the cache with a specified expiration time.

        Args:
            key (str): The key under which the verification code will be stored.
        
        Returns:
            dict: A result dictionary with key
        """
        verification_code = self.generate_verification_code()
        store = self.r.setex(key, 300, str(verification_code))
        if store:
            self.logger.info(store)
            return verification_code
        return False



    def get_verification_code(self, key: str) -> dict:
        """
        Get the verification code associated with the given key from the cache.

        Args:
            key (str): The key associated with the verification code to get the value

        Returns:
            dict:  A result dictionary with keys 'status' (str) and 'message' (str).
        """
        verification_code = self.r.get(key)
        if verification_code:
            # Ensure verification_code is decoded if it's a byte string
            if isinstance(verification_code, bytes):
                verification_code = verification_code.decode("utf-8")
                return verification_code
                # return {'status': 'success', 'message':  f'Retrieved verification code {verification_code} for {key}'}
        else:
            self.logger.info(f"No verification code found for {key}")
            return {'status': 'error', 'message': 'Failed to get verification code'}
        




    def del_verification_code(self, key:str) -> dict:
        """
        Delete the verification code associated with the given key from the cache.

        Args:
            key (str): The key associated with the verification code to be deleted.

        Returns:
            dict: A result dictionary with keys 'status' (str) and 'message' (str).
        """
        delete_verification_code = self.r.delete(key)
        if delete_verification_code:
            self.logger.info(f"Verification code deleted successfully for key: {key}")
            return {'status': 'success', 'message': 'Verification code deleted successfully'}
        else:
            self.logger.error(f"Failed to delete verification code for key: {key}")
            return {'status': 'error', 'message': 'Failed to delete verification code'}
        





