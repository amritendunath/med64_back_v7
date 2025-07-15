from fastapi import APIRouter, Depends, HTTPException, status, Request,Form
from fastapi.responses import RedirectResponse, JSONResponse
from typing import Optional
from services.email_service import EmailOAuth
from services.google_oauth import GoogleOAuth
from services.twitter_oauth import TwitterOAuth
from services.microsoft_auth import MicrosoftOAuth
# from services.phone import PhoneAuth
import logging


# import firebase_admin
from fastapi import FastAPI, Request
# from fastapi.middleware.cors import CORSMiddleware
# from firebase_admin import credentials, auth, initialize_app
from pydantic import BaseModel
# cred = credentials.Certificate("sathiaiagent-firebase-adminsdk-fbsvc-74faf8d590.json")
# firebase_admin.initialize_app(cred)
from authlib.integrations.starlette_client import OAuth
app = FastAPI()
app.secret_key = 'your-secret-key'
oauth = OAuth(app)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Create an APIRouter for auth routes
auth_router = APIRouter(prefix="", tags=["auth"])


class EmailVerificationRequest(BaseModel):
    email: str
    code: str 


# Dependency to access the oauth instance from app.state
def get_google_oauth(request: Request) -> GoogleOAuth:
    return request.app.state.google_oauth

def get_twitter_oauth(request: Request) -> TwitterOAuth:
    return request.app.state.twitter_oauth

def get_microsoft_oauth(request: Request) -> MicrosoftOAuth:
    return request.app.state.microsoft_oauth

def get_ses_oauth(request: Request)-> EmailOAuth:
    return request.app.state.email_oauth

# class TokenRequest(BaseModel):
#     idToken: str

# @auth_router.post("/verify-token")
# async def verify_token(data: TokenRequest):
#     try:
#         decoded_token = auth.verify_id_token(data.id_token)
#         uid = decoded_token["uid"]
#         return {"status": "success", "uid": uid}
#     except Exception as e:
#         return {"status": "error", "message": str(e)}
# Google OAuth routes

# @auth_router.get('/auth/twitter/login')
# def login():
#     redirect_uri = url_for('auth_callback', _external=True)
#     return twitter.authorize_redirect(redirect_uri)

# @auth_router.get('/auth/twitter/callback')
# def auth_callback():
#     token = twitter.authorize_access_token()
#     resp = twitter.get('account/verify_credentials.json')
#     profile = resp.json()
#     # Save user info or token in session or DB
#     return f"Hello {profile['screen_name']}"


@auth_router.get("/login/microsoft")
async def microsoft_login(request: Request, microsoft_oauth: MicrosoftOAuth =  Depends(get_microsoft_oauth)):
    try:
        # twitter_oauth = TwitterOAuth()
        return await microsoft_oauth.microsoft_login(request)
    except Exception as e:
        logging.error(f"Error in google_login: {e}")
        raise HTTPException(status_code=500, detail="An error occurred")


@auth_router.get("/auth/microsoft/callback", name="auth_microsoft_callback")
async def microsoft_authorize(request: Request, microsoft_oauth: MicrosoftOAuth =  Depends(get_microsoft_oauth)):
    try:
        # twitter_oauth = TwitterOAuth()
        return await microsoft_oauth.microsoft_authorize(request)
    except Exception as e:
        logging.error(f"Error in google_authorize: {e}")
        raise HTTPException(status_code=500, detail="An error occurred")




@auth_router.get("/login/twitter")
async def twitter_login(request: Request, twitter_oauth: TwitterOAuth =  Depends(get_twitter_oauth)):
    try:
        # twitter_oauth = TwitterOAuth()
        return await twitter_oauth.twitter_login(request)
    except Exception as e:
        logging.error(f"Error in google_login: {e}")
        raise HTTPException(status_code=500, detail="An error occurred")


@auth_router.get("/login/twitter/callback", name="auth_twitter_callback")
async def twitter_authorize(request: Request, twitter_oauth: TwitterOAuth =  Depends(get_twitter_oauth)):
    try:
        # twitter_oauth = TwitterOAuth()
        return await twitter_oauth.twitter_authorize(request)
    except Exception as e:
        logging.error(f"Error in google_authorize: {e}")
        raise HTTPException(status_code=500, detail="An error occurred")


@auth_router.get("/login/google")
async def google_login(request: Request, google_oauth: GoogleOAuth = Depends(get_google_oauth)):
    try:
        # google_oauth = GoogleOAuth()  # Create an instance of GoogleOAuth
        return await google_oauth.google_login(request)  # Call the method on the instance
    except Exception as e:
        logging.error(f"Error in google_login: {e}")
        raise HTTPException(status_code=500, detail="An error occurred")


@auth_router.get("/login/google/callback")
async def google_authorize(request: Request, google_oauth: GoogleOAuth = Depends(get_google_oauth)):
    try:
        # google_oauth = GoogleOAuth()
        return await google_oauth.google_authorize(request)
    except Exception as e:
        logging.error(f"Error in google_authorize: {e}")
        raise HTTPException(status_code=500, detail="An error occurred")



# AWS Email verification routes
@auth_router.post("/login/email_status")
async def verify_user_email(request: Request, email_service: EmailOAuth= Depends(get_ses_oauth)):
    try:
        verify  = await email_service._verify_sender_email(request)
        if verify == True:
            return JSONResponse({"status": True})
        else:
            return JSONResponse({"status": False})
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred")
    
@auth_router.post("/login/name_status")
async def verify_user_email(request: Request, email_service: EmailOAuth= Depends(get_ses_oauth)):
    try:
        verify = await email_service.check_name(request)
        return verify
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred")
    

@auth_router.post("/login/email")
async def send_email_verification_route(request: Request, email_service: EmailOAuth= Depends(get_ses_oauth)):
    try:
        verify =await email_service._verify_sender_email(request)
        if verify == True:
            sent = await email_service.send_verification_email(request)
        else:
            sent = JSONResponse(
                content={"message": "Email is not verified"},
                status_code=status.HTTP_400_BAD_REQUEST,
            )  # Provide a default value if not verified
        logging.info(sent)
        # return await {"sent": sent, "verify_user_email": verify}
        return sent
    except Exception as e:
        logging.error(f"Error in send_email_verification_route: {e}")
        raise HTTPException(status_code=500, detail="An error occurred")
    

@auth_router.post("/verify-email")
async def verify_email_endpoint(request: Request, email_service: EmailOAuth= Depends(get_ses_oauth)):
    try:
        verified =await email_service.verify_email(request)
        logging.info(verified)
        return verified
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred")


# Phone Routes
# @auth_router.post('/send-verification')
# async def send_phone_verification(phone_number: str = Form(...)):
#     try:
#         phone_auth = PhoneAuth()
#         return phone_auth.check_and_verify_phone_number(phone_number)
#     except Exception as e:
#         logging.error(f"Error in send_phone_verification: {e}")
#         raise HTTPException(status_code=500, detail="An error occurred")

# @auth_router.post("/verify-code")
# async def verify_phone_code(phone_number: str = Form(...), code: str = Form(...)):
#     try:
#         phone_auth = PhoneAuth()
#         return phone_auth.verify_sms_otp(phone_number, code)
#     except Exception as e:
#         logging.error(f"Error in verify_phone_code: {e}")
#         raise HTTPException(status_code=500, detail="An error occurred")


# @app.post("/send-verification-email/")
# async def send_verification_email_endpoint():
#     return await email_service.send_verification_email(email_data)


# from flask import jsonify, request
# from flask import Blueprint
# from services.email import EmailService
# from services.oauth import GoogleOAuth
# from services.phone import PhoneAuth
# import logging
# from flask import current_app



# # Configure logging
# logging.basicConfig(level=logging.INFO)

# # Create a Blueprint for auth routes
# auth_bp = Blueprint("auth", __name__)


# # Google OAuth routes
# @auth_bp.route("/login/google")
# def google_login():
#     try:
#         google_oauth = GoogleOAuth()  # Create an instance of GoogleOAuth
#         # google_oauth = current_app.extensions['google_oauth']
#         return google_oauth.google_login()  # Call the method on the instance
#     except Exception as e:
#         logging.error(f"Error in google_login: {e}")
#         return jsonify({"error": "An error occurred"}), 500


# @auth_bp.route("/login/google/callback")
# def google_authorize():
#     try:
#         google_oauth = GoogleOAuth()
#         # google_oauth = current_app.extensions['google_oauth']
#         return google_oauth.google_authorize()
#     except Exception as e:
#         logging.error(f"Error in google_authorize: {e}")
#         return jsonify({"error": "An error occurred"}), 500


# # Twilio Phone Routes
# @auth_bp.route('/send-verification', methods=['POST'])
# def send_phone_verification():
#     try:
#         data = request.get_json()
#         phone_number = data.get('phoneNumber')
#         phone_auth = PhoneAuth()
#         return phone_auth.check_and_verify_phone_number(phone_number)
#     except Exception as e:
#         logging.error(f"Error in send_phone_verification: {e}")
#         return jsonify({"error": "An error occurred"}), 500

# @auth_bp.route("/verify-code", methods=["POST"])
# def verify_phone_code():
#     try:
#         data = request.get_json()
#         phone_number = data.get('phoneNumber')
#         code = data.get("code")
#         phone_auth = PhoneAuth()
#         return phone_auth.verify_sms_otp(phone_number, code)
#     except Exception as e:
#         logging.error(f"Error in verify_phone_code: {e}")
#         return jsonify({"error": "An error occurred"}), 500


# # AWS Email verification routes
# @auth_bp.route("/send-email-verification", methods=["POST"])
# def send_email_verification_route():
#     try:
#         email_service = EmailService()
#         sent = email_service.send_verification_email()
#         verify_user_email = email_service._verify_sender_email()
#         logging.info(sent)
#         return sent, verify_user_email
#     except Exception as e:
#         logging.error(f"Error in send_email_verification_route: {e}")
#         return jsonify({"error": "An error occurred"}), 500


# @auth_bp.route("/verify-email", methods=["POST"])
# def verify_email_route():
#     try:
#         email_service = EmailService()
#         verify_email = email_service._verify_sender_email()
#         if verify_email:
#             using_otp = email_service.verify_email()
#             return using_otp
#         else:
#             None
#     except Exception as e:
#         logging.error(f"Error in verify_email_route: {e}")
#         return jsonify({"error": "An error occurred"}), 500


# @auth_bp.route("/verify-email", methods=["POST"])
# def verify_email_route():
#     try:
#         email_service = EmailService()
#         verify_email = email_service.verify_email()
#         if verify_email:
#             return verify_email
#         else:
#             return None
#     except Exception as e:
#         logging.error(f"Error in verify_email_route: {e}")
#         return jsonify({"error": "An error occurred"}), 500
