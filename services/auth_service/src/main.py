# # main.py
# from fastapi import FastAPI, HTTPException, Request
# from pydantic import BaseModel
# from firebase_auth import verify_firebase_token
# import uvicorn
# from fastapi.responses import JSONResponse

# app = FastAPI()

# class TokenRequest(BaseModel):
#     id_token: str

# @app.post("/auth/login")
# async def login(token_request: TokenRequest):
#     decoded_token = verify_firebase_token(token_request.id_token)
#     if not decoded_token:
#         raise HTTPException(status_code=401, detail="Invalid token")

#     # Example: create your own session/JWT here
#     user_info = {
#         "uid": decoded_token["uid"],
#         "email": decoded_token.get("email"),
#         "name": decoded_token.get("name"),
#     }

#     # Optionally store user info in DB
#     return JSONResponse({"message": "Login successful", "user": user_info})



# if __name__ == "__main__":
#     uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)



import os
import sys
import logging
import uvicorn
from datetime import timedelta
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config as StarletteConfig
from services.google_oauth import GoogleOAuth
from services.twitter_oauth import TwitterOAuth
from services.microsoft_auth import MicrosoftOAuth
from services.email_service import EmailOAuth
from routes.auth_routes import auth_router
from utils.database import Database
from utils.helpers import RouteUpdater
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set to DEBUG to capture more detailed logs
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def create_app():
    
    middleware = [
        Middleware(SessionMiddleware, secret_key=os.environ.get("JWT_SECRET", os.urandom(24).hex())),
    ]
    app = FastAPI(middleware=middleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Access configurations from environment variables
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
    TWITTER_CLIENT_ID = os.environ.get('TWITTER_CLIENT_ID')
    TWITTER_CLIENT_SECRET = os.environ.get('TWITTER_CLIENT_SECRET')
    MICROSOFT_CLIENT_ID =os.environ.get('MICROSOFT_CLIENT_ID')
    MICROSOFT_CLIENT_SECRET = os.environ.get('MICROSOFT_CLIENT_SECRET')
    JWT_SECRET = os.environ.get("JWT_SECRET")
    AWS_SES=os.environ.get("AWS_SES")
    AWS_ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY_ID")
    AWS_SECRET_KEY=os.environ.get("AWS_SECRET_ACCESS_KEY")
    REGION_NAME=os.environ.get("AWS_REGION")
    AWS_SENDER_EMAIL=os.environ.get("SES_SENDER_EMAIL")

    starlette_config = StarletteConfig(environ=os.environ)
    oauth = OAuth(starlette_config)
    db = Database()
    helper = RouteUpdater()

    # Create an instance of GoogleOAuth with all required arguments
    google_oauth = GoogleOAuth(
        logger=logger,
        oauth=oauth,
        google_client_id=GOOGLE_CLIENT_ID,
        google_client_secret=GOOGLE_CLIENT_SECRET,
        helper=helper,
        db=db
    )
    twitter_oauth = TwitterOAuth(
        logger=logger,
        oauth=oauth,
        twitter_client_id=TWITTER_CLIENT_ID,
        twitter_client_secret=TWITTER_CLIENT_SECRET,
        helper=helper,
        db=db
    )
    microsoft_oauth = MicrosoftOAuth(
        logger=logger,
        oauth=oauth,
        microsoft_client_id=MICROSOFT_CLIENT_ID,
        microsoft_client_secret=MICROSOFT_CLIENT_SECRET,
        helper=helper,
        db=db
    )
    email_oauth = EmailOAuth(
        service_name=AWS_SES,
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=REGION_NAME,
        jwt_secret=JWT_SECRET,
        sender_email = AWS_SENDER_EMAIL,
        helper=helper,
        db=db
    )
    app.state.google_oauth = google_oauth
    app.state.twitter_oauth = twitter_oauth
    app.state.microsoft_oauth = microsoft_oauth
    app.state.email_oauth = email_oauth
    app.include_router(auth_router)
    
    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5004)










# import os
# import sys
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# import logging
# from datetime import timedelta
# from flask import Flask
# from flask_cors import CORS
# from flask_jwt_extended import JWTManager
# from authlib.integrations.flask_client import OAuth
# from services.oauth import GoogleOAuth
# from routes.auth_routes import auth_bp
# from utils.database import Database
# from utils.helpers import RouteUpdater
# from config import Config

# logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)
# handler = logging.StreamHandler(sys.stdout)
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# handler.setFormatter(formatter)
# logger.addHandler(handler)


# # backend/auth/src/main.py
# def create_app():
#     app = Flask(__name__)
#     CORS(app, supports_credentials=True, origins=["*"])
#     app.config.from_object(Config)

#     # Access configurations from app.config
#     google_client_id = app.config["GOOGLE_CLIENT_ID"]
#     google_client_secret = app.config["GOOGLE_CLIENT_SECRET"]

#     # Check if the credentials are loaded correctly
#     if not google_client_id or not google_client_secret:
#         logger = logging.getLogger(__name__)
#         logger.error("Google credentials are not set in the configuration.")
#         sys.exit(1)

#     oauth = OAuth(app)
#     db = Database()
#     helper = RouteUpdater()

#     # Configuration
#     app.secret_key = os.environ.get("JWT_SECRET_KEY", os.urandom(24))
#     app.config["SESSION_TYPE"] = "filesystem"
#     app.config["SESSION_COOKIE_SECURE"] = True
#     app.config["SESSION_COOKIE_HTTPONLY"] = True
#     app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
#     JWTManager(app)

#     app.register_blueprint(auth_bp)  # Pass google_oauth instance
#     # Create an instance of GoogleOAuth with all required arguments
#     google_oauth = GoogleOAuth(
#         logger=logging.getLogger(__name__),
#         app=app,
#         oauth=oauth,
#         google_client_id=google_client_id,
#         google_client_secret=google_client_secret,
#         helper=helper,
#         db=db
#     )
#     app.extensions['google_oauth'] = google_oauth
#     return app


# if __name__ == "__main__":
#     app = create_app()
#     app.run(host="0.0.0.0", port=5004, debug=True)
# @app.route('/phone')
# def index():
#     user = session.get('user')
#     if user:
#         return  f'Hello, {user["email"]}. <a href="/logout">Logout</a>'
#     else:
#         return f'Welcome! Please <a href="/login">Login</a>.'

# @app.route('/login/phone')
# def login():
#     # Alternate option to redirect to /authorize
#     redirect_uri = url_for('authorize', _external=True)
#     return oauth.oidc.authorize_redirect(redirect_uri)
#     # return oauth.oidc.authorize_redirect('https://d84l1y8p4kdic.cloudfront.net')

# for aws sns and congnito---------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# @app.route('/login/phone')
# def phone_login():
#     return oauth.oidc.authorize_redirect('https://d84l1y8p4kdic.cloudfront.net')

# @app.route('/login/phone/callback')
# def phone_callback():  # Changed from 'authorize' to 'phone_callback'
#     try:
#         token = oauth.oidc.authorize_access_token()
#         user = token['userinfo']
#         session['user'] = user

#         access_token = create_access_token(
#             identity=user.get('email'),
#             additional_claims={
#                 'phone': user.get('phone_number'),
#                 'auth_provider': 'phone'
#             }
#         )

#         return redirect('https://d84l1y8p4kdic.cloudfront.net/auth-callback?token=' + access_token)
#     except Exception as e:
#         return redirect('https://d84l1y8p4kdic.cloudfront.net/auth-callback?error=Authentication failed')
# @app.route('/login/phone/callback')
# def authorize():
#     try:
#         token = oauth.oidc.authorize_access_token()
#         user = token['userinfo']
#         session['user'] = user

#         # Create JWT token with claims
#         access_token = create_access_token(
#             identity=user.get('email'),
#             additional_claims={
#                 'phone': user.get('phone_number'),
#                 'auth_provider': 'phone'
#             }
#         )

#         frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
#         redirect_url = f"{frontend_url}/auth-callback?token={access_token}"
#         return redirect(redirect_url)
#     except Exception as e:
#         frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
#         error_redirect = f"{frontend_url}/auth-callback?error=Authentication failed"
#         return redirect(error_redirect)
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# In-memory user store (replace with database in production)
# users = {}

# @app.route('/register', methods=['POST'])
# def register():
#     data = request.get_json()
#     username = data.get('username')
#     password = data.get('password')

#     if not username or not password:
#         return jsonify({"error": "Missing username or password"}), 400

#     if username in users:
#         return jsonify({"error": "Username already exists"}), 409

#     users[username] = generate_password_hash(password)
#     return jsonify({"message": "User registered successfully"}), 201

# @app.route('/login', methods=['POST'])
# def login():
#     data = request.get_json()
#     username = data.get('username')
#     password = data.get('password')

#     if not username or not password:
#         return jsonify({"error": "Missing username or password"}), 400

#     stored_password = users.get(username)
#     if not stored_password or not check_password_hash(stored_password, password):
#         return jsonify({"error": "Invalid credentials"}), 401

#     access_token = create_access_token(identity=username)
#     return jsonify({"token": access_token}), 200
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# @app.route('/protected', methods=['GET'])
# @jwt_required()
# def protected():
#     current_user = get_jwt_identity()
#     return jsonify({"logged_in_as": current_user}), 200

# @app.route('/verify-token', methods=['GET'])
# @jwt_required()
# def verify_token():
#     current_user = get_jwt_identity()
#     return jsonify({
#         "valid": True,
#         "user": current_user,
#         "message": "Token is valid"
#     }), 200

# @app.route('/verify-phone', methods=['POST'])
# def verify_phone():
#     try:
#         data = request.get_json()
#         phone_number = data.get('phoneNumber')
#         verification_code = data.get('verificationCode')

#         # Verify the phone number with Firebase
#         # user = auth.sign_in_with_phone_number(phone_number, verification_code)
#         user = auth.verify_id_token(phone_number, verification_code)

#         # Create JWT token after successful verification
#         access_token = create_access_token(identity=phone_number)

#         return jsonify({
#             "token": access_token,
#             "message": "Phone verification successful"
#         }), 200

#     except Exception as e:
#         return jsonify({
#             "error": str(e),
#             "message": "Phone verification failed"
#         }), 400
