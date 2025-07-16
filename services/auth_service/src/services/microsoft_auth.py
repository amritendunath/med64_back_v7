from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware
import os



import os
import logging
from fastapi import Request
from fastapi.responses import RedirectResponse 
from jose import jwt

class MicrosoftOAuth:
    def __init__(self, logger, oauth, microsoft_client_id, microsoft_client_secret, helper, db):
        """
        Initialize the Microsoft OAuth service.

        Args:
            logger (logging.Logger): Logger instance.
            oauth (OAuth): OAuth instance.
            microsoft_client_id (str): Microsoft Client ID.
            microsoft_client_secret (str): Microsoft Client Secret.
            helper (RouteUpdater): Route updater instance.
            db (Database): Database instance.
        """
        self.logger = logger
        self.oauth = oauth
        self.helper = helper
        self.db = db

        # Debugging: Log the type and value of microsoft_client_secret
        self.logger.debug(f"MICROSOFT_CLIENT_SECRET type: {type(microsoft_client_id)}")
        self.logger.debug(f"MICROSOFT_CLIENT_SECRET value: {microsoft_client_secret}")

        # Ensure microsoft_client_secret is a string
        if not isinstance(microsoft_client_secret, str):
            self.logger.error("microsoft_client_secret must be a string.")
            raise ValueError("microsoft_client_secret must be a string.")

        # Register the Microsoft OAuth provider
        self.microsoft = self.oauth.register(
            name='microsoft',
            client_id=microsoft_client_id,
            client_secret=microsoft_client_secret,
            access_token_url='https://login.microsoftonline.com/ac310a0c-6e9b-4b3d-9114-855d9cfd596b/oauth2/v2.0/token',
            access_token_params=None,
            authorize_url='https://login.microsoftonline.com/ac310a0c-6e9b-4b3d-9114-855d9cfd596b/oauth2/v2.0/authorize',
            authorize_params={"response_type": "code"},
            api_base_url='https://graph.microsoft.com/v1.0/',
            client_kwargs={'scope': 'openid email profile User.Read'},
)

    async def microsoft_login(self, request: Request):
        """
        Initiate the Microsoft OAuth login process.

        Returns:
            redirect: Redirects the client to the Microsoft authorization URL.
        """
        redirect_uri = request.url_for('auth_microsoft_callback')
        return await self.microsoft.authorize_redirect(request, redirect_uri)

    async def microsoft_authorize(self, request: Request):
        """
        Handle the callback from Microsoft after authorization.

        Returns:
            redirect: Redirects the client to the frontend URL with a token or error message.
        """
        try:
            token = await self.microsoft.authorize_access_token(request)
            api_base_url = 'https://graph.microsoft.com/v1.0/'
            resp = await self.microsoft.get(api_base_url, token=token)
            user_info = resp.json()
            self.logger.info(f"User Info: {user_info}")

            # Check if user exists in the database
            user = self.db.users.find_one(
                {"email": {"$regex": f"^{user_info['screen_name']}$", "$options": "i"}},
            )
            self.logger.info(f"User: {user}")

            if not user:
                user_ehr_id = self.helper.get_next_ehr_id()

                new_user = {
                    "email": user_info["screen_name"],
                    "name": user_info["name"],
                    "picture": user_info["profile_image_url_https"],
                    "auth_provider": "Microsoft",
                    "user_ehr_id": str(user_ehr_id),
                }
                self.db.insert_user(new_user)

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
                    "name": user_info["name"],
                    "picture": user_info["profile_image_url_https"],
                    "auth_provider": "Microsoft",
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
            self.logger.error(f"Error during Microsoft authorization: {str(e)}")
            frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3000")
            error_redirect = f"{frontend_url}/auth-callback?error=Authentication+failed"
            return RedirectResponse(error_redirect)