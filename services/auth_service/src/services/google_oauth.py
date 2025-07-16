import os
import logging
from fastapi import Request
from fastapi.responses import RedirectResponse 
from jose import jwt

class GoogleOAuth:
    def __init__(self, logger, oauth, google_client_id, google_client_secret, helper, db):
        """
        Initialize the Google OAuth service.

        Args:
            logger (logging.Logger): Logger instance.
            oauth (OAuth): OAuth instance.
            google_client_id (str): Google Client ID.
            google_client_secret (str): Google Client Secret.
            helper (RouteUpdater): Route updater instance.
            db (Database): Database instance.
        """
        self.logger = logger
        self.oauth = oauth
        self.helper = helper
        self.db = db

        # Debugging: Log the type and value of google_client_secret
        self.logger.debug(f"GOOGLE_CLIENT_SECRET type: {type(google_client_secret)}")
        self.logger.debug(f"GOOGLE_CLIENT_SECRET value: {google_client_secret}")

        # Ensure google_client_secret is a string
        if not isinstance(google_client_secret, str):
            self.logger.error("GOOGLE_CLIENT_SECRET must be a string.")
            raise ValueError("GOOGLE_CLIENT_SECRET must be a string.")

        # Register the Google OAuth provider
        self.google = self.oauth.register(
            name="google",
            client_id=google_client_id,
            client_secret=google_client_secret,
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            api_base_url="https://www.googleapis.com/oauth2/v2/",
            client_kwargs={"scope": "openid email profile", "prompt": "select_account"},
        )

    async def google_login(self, request: Request):
        """
        Initiate the Google OAuth login process.

        Returns:
            redirect: Redirects the client to the Google authorization URL.
        """
        redirect_uri = request.url_for('google_authorize')
        return await self.google.authorize_redirect(request, redirect_uri)

    async def google_authorize(self, request: Request):
        """
        Handle the callback from Google after authorization.

        Returns:
            redirect: Redirects the client to the frontend URL with a token or error message.
        """
        try:
            token = await self.google.authorize_access_token(request)
            api_base_url = "https://www.googleapis.com/oauth2/v2/userinfo"
            resp = await self.google.get(api_base_url, token=token)
            user_info = resp.json()
            self.logger.info(f"User Info: {user_info}")

            # Check if user exists in the database
            user = self.db.users.find_one(
                {"email": {"$regex": f"^{user_info['email']}$", "$options": "i"}},
            )
            self.logger.info(f"User: {user}")

            if not user:
                user_ehr_id = self.helper.get_next_ehr_id()

                new_user = {
                    "email": user_info["email"],
                    "name": user_info["name"],
                    "picture": user_info["picture"],
                    "auth_provider": "google",
                    "user_ehr_id": str(user_ehr_id),
                }
                self.db.insert_user(new_user)
                jwt_secret = os.environ.get("JWT_SECRET")
                access_token = jwt.encode(
                claims={
                    "sub": user_info["email"],
                    "name": user_info.get("name"),
                    "picture": user_info.get("picture"),
                    "auth_provider": "google",
                    "user_ehr_id": user_ehr_id,
                },
                key=jwt_secret,
                algorithm="HS256",
            )
            elif user:
                user_ehr_id = user.get("user_ehr_id")
                self.logger.info(f"User EHR ID: {user_ehr_id}")

                # Ensure JWT_SECRET is set and is a string
                jwt_secret = os.environ.get("JWT_SECRET")
                if not jwt_secret:
                    self.logger.error("JWT_SECRET is not set in the configuration.")
                    raise ValueError("JWT_SECRET is not set in the configuration.")
                if not isinstance(jwt_secret, str):
                    self.logger.error("JWT_SECRET must be a string.")
                    raise ValueError("JWT_SECRET must be a string.")

            # Create JWT token
                access_token = jwt.encode(
                    claims={
                        "sub": user_info["email"],
                        "name": user_info.get("name"),
                        "picture": user_info.get("picture"),
                        "auth_provider": "google",
                        "user_ehr_id": user_ehr_id,
                    },
                    key=jwt_secret,
                    algorithm="HS256",
                )
            self.logger.info(f"Access Token: {access_token}")

            frontend_url = os.environ.get("FRONTEND_URL")
            redirect_url = f"{frontend_url}/auth-callback?token={access_token}"
            return RedirectResponse(redirect_url)

        except Exception as e:
            self.logger.error(f"Error during Google authorization: {str(e)}")
            frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3000")
            error_redirect = f"{frontend_url}/auth-callback?error=Authentication+failed"
            return RedirectResponse(error_redirect)



# import os
# import logging
# import hashlib
# from flask_cors import CORS
# from flask import Flask, redirect, url_for, abort, current_app
# from flask_jwt_extended import create_access_token, JWTManager
# from authlib.integrations.flask_client import OAuth
# from utils.database import Database
# from utils.helpers import RouteUpdater
# from datetime import timedelta


# class GoogleOAuth:
#     # def __init__(self, logger = logger, app=app, oauth=oauth, google_client_id = google_client_id, google_client_secret = google_client_secret, helper =helper, db=db):
#     def __init__(self, logger, app, oauth, google_client_id, google_client_secret , helper , db):
#         """
#         Initialize the Google OAuth service.

#         Args:
#             logger (logging.Logger): Logger instance.
#             app (Flask): Flask application instance.
#             oauth (OAuth): OAuth instance.
#             google_client_id (str): Google Client ID.
#             google_client_secret (str): Google Client Secret.
#             helper (RouteUpdater): Route updater instance.
#             db (Database): Database instance.
#         """
#         self.logger = logger
#         self.app = app
#         self.oauth = oauth
#         self.helper = helper
#         self.db = db
#         self.google = self.oauth.register(
#             name="google",
#             client_id= google_client_id,
#             client_secret= google_client_secret,
#             server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
#             api_base_url="https://www.googleapis.com/oauth2/v2/",
#             client_kwargs={"scope": "openid email profile", "prompt": "select_account"},
#         )

#     def google_login(self):
#         """
#         Initiate the Google OAuth login process.

#         Returns:
#             redirect: Redirects the client to the Google authorization URL.
#         """

#         return self.google.authorize_redirect(redirect_uri=url_for('auth.google_authorize', _external=True))

#     def google_authorize(self):
#         """
#         Handle the callback from Google after authorization.

#         Returns:
#             redirect: Redirects the client to the frontend URL with a token or error message.
#         """
#         try:
#             token = self.google.authorize_access_token()
            # api_base_url = "https://www.googleapis.com/oauth2/v2/userinfo"
            # resp = self.google.get(api_base_url, token=token)
            # user_info = resp.json()
            # self.logger.info(user_info)
#             # Check if user exists in the database
#             user = self.db.users.find_one(
#                 {"email": {"$regex": "^" + user_info["email"] + "$", "$options": "i"}},
#             )
#             self.logger.info(f"User: {user}")
#             if not user:
#                 user_ehr_id = self.helper.get_next_ehr_id()

#                 new_user = {
#                     "email": user_info["email"],
#                     "name": user_info.get("name"),
#                     "picture": user_info.get("picture"),
#                     "auth_provider": "google",
#                     "user_ehr_id": str(user_ehr_id),
#                 }
#                 self.db.insert_user(new_user)

#             user_ehr_id = user.get("user_ehr_id")
#             self.logger.info(f"User EHR ID: {user_ehr_id}")

#             access_token = create_access_token(
#                 identity=user_info["email"],
#                 additional_claims={
#                     "name": user_info.get("name"),
#                     "picture": user_info.get("picture"),
#                     "auth_provider": "google",
#                     "user_ehr_id": user_ehr_id,
#                 },
#             )
#             self.logger.info(f"Access Token: {access_token}")
#             frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
#             redirect_url = f"{frontend_url}/auth-callback?token={access_token}"
#             return redirect(redirect_url)

#         except Exception as e:
#             self.logger.error(f"Error during Google authorization: {str(e)}")
#             frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
#             error_redirect = f"{frontend_url}/auth-callback?error=Authentication failed"
#             return redirect(error_redirect)
# logger = logging.getLogger(__name__)
# app = Flask(__name__)
# oauth = OAuth(app)
# db = Database()
# helper = RouteUpdater()
# CORS(app, supports_credentials=True, origins=["http://localhost:3000"])

# app.secret_key = os.environ.get("JWT_SECRET_KEY", os.urandom(24))
# app.config["SESSION_TYPE"] = "filesystem"
# app.config["SESSION_COOKIE_SECURE"] = True
# app.config["SESSION_COOKIE_HTTPONLY"] = True
# app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
# google_client_id = app.config["GOOGLE_CLIENT_ID"] = os.getenv("GOOGLE_CLIENT_ID")
# google_client_secret = app.config["GOOGLE_CLIENT_SECRET"] = os.getenv("GOOGLE_CLIENT_SECRET")

        # state_token = self.helper.generate_state_token()
        # self.logger.info(f"state_token: {state_token}")
        # redirect_url = url_for("auth.google_authorize", _external=True)
        # return self.google.authorize_redirect(
        #     redirect_uri=redirect_url, state = state_token
        # )
        # return self.google.authorize_redirect(
        #     url_for("auth.google_authorize", _external=True)
        # )