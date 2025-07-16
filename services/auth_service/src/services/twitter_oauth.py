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

class TwitterOAuth:
    def __init__(self, logger, oauth, twitter_client_id, twitter_client_secret, helper, db):
        """
        Initialize the Twitter OAuth service.

        Args:
            logger (logging.Logger): Logger instance.
            oauth (OAuth): OAuth instance.
            twitter_client_id (str): Twitter Client ID.
            twitter_client_secret (str): Twitter Client Secret.
            helper (RouteUpdater): Route updater instance.
            db (Database): Database instance.
        """
        self.logger = logger
        self.oauth = oauth
        self.helper = helper
        self.db = db

        # Debugging: Log the type and value of twitter_client_secret
        self.logger.debug(f"TWITTER_CLIENT_SECRET type: {type(twitter_client_secret)}")
        self.logger.debug(f"TWITTER_CLIENT_SECRET value: {twitter_client_secret}")

        # Ensure twitter_client_secret is a string
        if not isinstance(twitter_client_secret, str):
            self.logger.error("twitter_client_secret must be a string.")
            raise ValueError("twitter_client_secret must be a string.")

        # Register the Twitter OAuth provider
        self.twitter = self.oauth.register(
            name='twitter',
            client_id=twitter_client_id,
            client_secret=twitter_client_secret,
            request_token_url='https://api.twitter.com/oauth/request_token',
            request_token_params=None,
            access_token_url='https://api.twitter.com/oauth/access_token',
            access_token_params=None,
            authorize_url='https://api.twitter.com/oauth/authenticate',
            api_base_url='https://api.twitter.com/1.1/account/verify_credentials.json',
            client_kwargs=None
)

    async def twitter_login(self, request: Request):
        """
        Initiate the Twitter OAuth login process.

        Returns:
            redirect: Redirects the client to the Twitter authorization URL.
        """
        redirect_uri = request.url_for('auth_twitter_callback')
        return await self.twitter.authorize_redirect(request, redirect_uri)

    async def twitter_authorize(self, request: Request):
        """
        Handle the callback from Twitter after authorization.

        Returns:
            redirect: Redirects the client to the frontend URL with a token or error message.
        """
        try:
            token = await self.twitter.authorize_access_token(request)
            api_base_url = 'https://api.twitter.com/1.1/account/verify_credentials.json'
            resp = await self.twitter.get(api_base_url, token=token)
            user_info = resp.json()
            self.logger.info(f"User Info: {user_info}")

            # Use screen_name as the unique identifier
            # twitter_id = user_info['screen_name']
            # Check if user exists in the database
            user = self.db.users.find_one(
                {"email": {"$regex": f"^{user_info['screen_name']}$", "$options": "i"}},
            )
            # user = self.db.users.find_one(
            # {"auth_provider_id": twitter_id, "auth_provider": "Twitter"}
            # )
            self.logger.info(f"User: {user}")

            if not user:
                user_ehr_id = self.helper.get_next_ehr_id()

                new_user = {
                    "email": user_info["screen_name"],
                    "name": user_info["name"],
                    "picture": user_info["profile_image_url_https"],
                    "auth_provider": "Twitter",
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
                    "auth_provider": "Twitter",
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
            self.logger.error(f"Error during Twitter authorization: {str(e)}")
            frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3000")
            error_redirect = f"{frontend_url}/auth-callback?error=Authentication+failed"
            return RedirectResponse(error_redirect)