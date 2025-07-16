from fastapi import APIRouter, Depends, HTTPException, status, Request,Form
from fastapi.responses import RedirectResponse, JSONResponse
from typing import Optional
from services.email_service import EmailOAuth
from services.google_oauth import GoogleOAuth
from services.twitter_oauth import TwitterOAuth
from services.microsoft_auth import MicrosoftOAuth
# from services.phone import PhoneAuth
import logging
from fastapi import FastAPI, Request
from pydantic import BaseModel
from authlib.integrations.starlette_client import OAuth

app = FastAPI()
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
