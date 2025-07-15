import boto3
import os
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import logging
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from jose import jwt
from datetime import datetime, timedelta
import sys
import os



# Add the project root directory to the PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()
logger = logging.getLogger(__name__)


# Replace Flask request with Pydantic model for request body
class EmailVerificationRequest(BaseModel):
    email: str
    code: Optional[str] = None

class EmailOAuth:
    def __init__(self,service_name, aws_access_key_id, aws_secret_access_key, region_name, jwt_secret, sender_email, helper, db):
        try:
            self.service_name=service_name
            self.aws_access_key_id = aws_access_key_id
            self.aws_secret_access_key = aws_secret_access_key
            self.region_name = region_name
            self.jwt_secret = jwt_secret
            self.sender_email = sender_email
            self.helper = helper
            self.db = db
            
            self.ses_client = boto3.client(
                service_name=self.service_name,
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.region_name
            )
        except Exception as e:
            logger.error(f"Failed to initialize SES client: {str(e)}")
            raise

    # async def send_verification_email(self, email_data: EmailVerificationRequest):
    async def send_verification_email(self, request: Request):
        CHARSET = "UTF-8"

        try:
            # email = email_data.email
            data = await request.json()
            email = data['email']
            logger.info(f"email:{email}")

            verification_code = self.helper.store_verification_code(email)
            logger.info(f"verification_code{verification_code}")

            response = self.ses_client.send_email(
                Source=self.sender_email,
                Destination={"ToAddresses": [email]},
                Message={
                    "Subject": {"Charset": CHARSET, "Data": "Email Verification Code"},
                    "Body": {
                        "Html": {
                            "Charset": CHARSET,
                            "Data": f"""
                                <html>
                                <head></head>
                                <body>
                                    <h1>Welcome to Sathi.ai</h1>
                                    <p>Your verification code is: <strong>{verification_code}</strong></p>
                                    <p>This code will expire in 10 minutes.</p>
                                </body>
                                </html>
                            """,
                        }
                    },
                },
            )
            logger.info(f"Email sent! Message ID: {response['MessageId']}")

            return JSONResponse(
                content={
                    "message": "Email sent successfully",
                    "message_id": response["MessageId"],
                },
                status_code=status.HTTP_200_OK,
            )

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            logger.error(f"Error ({error_code}): {error_message}")
            raise HTTPException(status_code=500, detail=f"Error sending email: {error_message}")

    async def _verify_sender_email(self, request: Request):
        try:
            region_name= self.region_name
            data = await request.json()
            sender_email = data['email']
            # sender_email = email
            response = self.ses_client.get_identity_verification_attributes(
                Identities=[sender_email]
            )
            verification_attrs = response.get("VerificationAttributes", {})

            status = verification_attrs.get(sender_email, {}).get(
                "VerificationStatus", "NotVerified"
            )
            if status == "Success":
                logger.info(
                    f"Email {sender_email} is already verified in region {region_name}, {status}"
                )
                return True
            elif status == "Pending":
                logger.info(
                    f"Verification for {sender_email} is pending in region {region_name}. Check your email inbox. {status}"
                )
                return False
            else:
                # Send verification request
                self.ses_client.verify_email_identity(EmailAddress=sender_email)
                logger.info(
                    f"Verification request sent to {sender_email} in region {region_name}"
                )
                logger.info(f"Please check your inbox and click the verification link")
                return False

        except ClientError as e:
            logger.error(f"Error verifying sender email: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error verifying sender email: {str(e)}")
        
    async def check_name(self, request: Request):
        """
        Check if the user has a name in the database.
        """
        try:
            email = (await request.json()).get("email")
            if not email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Email is required"
                )
            # Assuming route_updater.get_user retrieves user data including name
            user = self.db.users.find_one(
            {"email": {"$regex": f"^{email}$", "$options": "i"}},
            )
            name = user['name']
            if user and name: 
                return {
                    "status": True,
                    "name": name
                }
            else:
                return False  # User does not have a name
        except Exception as e:
            logger.error(f"Error checking user name: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error checking user name: {str(e)}",
            )
            

    async def verify_email(self, request: Request):
        try:
            data = await request.json()
            email = data.get("email")
            code = data.get("verificationCode")
            name = data.get("name")
            logger.info(name, email, code)
            if not name or not email or not code:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email and code and Name are required",
                )

            stored_code = self.helper.get_verification_code(email)
            logger.info(f"stored_code:{stored_code}")

            if not stored_code:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No verification code found",
                )

            if code == stored_code:
                # Remove the used verification code
                logger.info(f"Verification code for {name} and {email} is {stored_code} and enteredCode {code}")
                user = self.db.users.find_one(
                {"email": {"$regex": f"^{email}$", "$options": "i"}},
                )
                if not user:
                    user_ehr_id = self.helper.get_next_ehr_id()
                    logger.info(user_ehr_id)

                    new_user = {
                        "email": email,
                        "name": name,
                        "auth_provider": "AWS",
                        "user_ehr_id": str(user_ehr_id),
                    }
                    token = self.create_jwt_token(name=name, email = email, user_ehr_id= user_ehr_id)
                    self.db.insert_user(new_user)

                elif user:
                    user_ehr_id = user["user_ehr_id"]
                    name = user["name"]
                    email = user["email"]
                    token = self.create_jwt_token(name, email, user_ehr_id)
                    logger.info(f"access_token{token}")
                    # route_updater.del_verification_code(email)

                return JSONResponse(
                    content={
                        "token": token,
                        "message": "Email verified successfully",
                    },
                    status_code=status.HTTP_200_OK,
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid verification code",
                )

        except HTTPException as http_exception:
            raise http_exception
        except Exception as e:
            logger.error(f"Email verification failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Email verification failed: {str(e)}",
            )

    def create_jwt_token(self,name:str, email: str, user_ehr_id: str):
        payload = {
            "name": name,
            "sub": email,
            "verified": True,
            "auth_provider": "AWS SES",
            "user_ehr_id": user_ehr_id
        }
        secret_key = self.jwt_secret  # Replace with your actual secret key
        if not isinstance(secret_key, str):
            raise ValueError("JWT_SECRET must be a string")
        algorithm = "HS256"  # You can choose a different algorithm if needed
        token = jwt.encode(payload, secret_key, algorithm=algorithm)
        return token  




# ... previous code ...

# if __name__ == "__main__":
#     async def main():
#         email = "testingboy93@gmail.com"
#         test_send = EmailService()
#         try:
#             verify = test_send._verify_sender_email()
#             if verify == "Success":
#                 sent = test_send.send_verification_email(email)
#                 print(sent) 


#         except Exception as e:
#             print(f"Error: {e}")

#     asyncio.run(main())


# import boto3
# import os
# from botocore.exceptions import ClientError
# from dotenv import load_dotenv
# import logging
# from flask import request, jsonify
# from flask_jwt_extended import create_access_token
# from utils.helpers import RouteUpdater

# load_dotenv()
# logger = logging.getLogger(__name__)
# route_updater = RouteUpdater()


# class EmailService:
#     def __init__(self):
#         try:
#             self.ses_client = boto3.client(
#                 "ses",
#                 aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
#                 aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
#                 region_name=os.getenv("AWS_REGION"),
#             )
#             # Verify sender email if not already verified
#             self._verify_sender_email()
#         except Exception as e:
#             logger.error(f"Failed to initialize SES client: {str(e)}")
#             raise

#     def send_verification_email(self):
#         CHARSET = "UTF-8"

#         try:
#             data = request.get_json()
#             email = data.get("email")
#             logger.info(f"email:{email}")

#             verification_code = route_updater.store_verification_code(email)
#             logger.info(f"verification_code{verification_code}")

#             # if email and verification_code:
#             #     return f"Email:{email} and Code:{verification_code} created and stored successfully"

#             response = self.ses_client.send_email(
#                 Source=os.getenv("SES_SENDER_EMAIL"),
#                 Destination={"ToAddresses": [email]},
#                 Message={
#                     "Subject": {"Charset": CHARSET, "Data": "Email Verification Code"},
#                     "Body": {
#                         "Html": {
#                             "Charset": CHARSET,
#                             "Data": f"""
#                                 <html>
#                                 <head></head>
#                                 <body>
#                                     <h1>Welcome to Sathi.ai</h1>
#                                     <p>Your verification code is: <strong>{verification_code}</strong></p>
#                                     <p>This code will expire in 10 minutes.</p>
#                                 </body>
#                                 </html>
#                             """,
#                         }
#                     },
#                 },
#             )
#             logger.info(f"Email sent! Message ID: {response['MessageId']}")

#             return (
#                 jsonify(
#                     {
#                         "message": "Email sent successfully",
#                         "message_id": response["MessageId"],
#                     }
#                 ),
#                 200,
#             )

#         except ClientError as e:
#             error_code = e.response["Error"]["Code"]
#             error_message = e.response["Error"]["Message"]
#             logger.error(f"Error ({error_code}): {error_message}")
#             return False

#     def _verify_sender_email(self, region_name="us-east-1"):
#         try:
#             sender_email = os.getenv("SES_SENDER_EMAIL")
#             response = self.ses_client.get_identity_verification_attributes(
#                 Identities=[sender_email]
#             )
#             verification_attrs = response.get("VerificationAttributes", {})

#             status = verification_attrs.get(sender_email, {}).get(
#                 "VerificationStatus", "NotVerified"
#             )
#             if status == "Success":
#                 logger.info(
#                     f"Email {sender_email} is already verified in region {region_name}"
#                 )
#                 return True
#             elif status == "Pending":
#                 logger.info(
#                     f"Verification for {sender_email} is pending in region {region_name}. Check your email inbox."
#                 )
#                 return False
#             else:
#                 # Send verification request
#                 self.ses_client.verify_email_identity(EmailAddress=sender_email)
#                 logger.info(
#                     f"Verification request sent to {sender_email} in region {region_name}"
#                 )
#                 logger.info(f"Please check your inbox and click the verification link")
#                 return False

#             # if sender_email not in verified_emails.get('VerifiedEmailAddresses', []):
#             #     self.ses_client.verify_email_identity(EmailAddress=sender_email)
#             #     logger.info(f"Verification request sent to sender email: {sender_email}")
#         except ClientError as e:
#             logger.error(f"Error verifying sender email: {str(e)}")

#     def verify_email(self):
#         try:
#             data = request.get_json()
#             email = data.get("email")
#             code = data.get("code")

#             if not email or not code:
#                 return jsonify({"error": "Email and code are required"}), 400

#             stored_code = route_updater.get_verification_code(email)
#             logger.info(f"stored_code:{stored_code}")

#             if not stored_code:
#                 return jsonify({"error": "No verification code found"}), 400

#             if code == stored_code:
#                 # Remove the used verification code
#                 logger.info(f"Verification code for email {email} has been deleted")

#                 # Create JWT token
#                 access_token = create_access_token(
#                     identity=email,
#                     additional_claims={
#                         "email": email,
#                         "verified": True,
#                         "auth_provider": email,
#                     },
#                 )
#                 route_updater.del_verification_code(email)

#                 return (
#                     jsonify(
#                         {
#                             "token": access_token,
#                             "message": "Email verified successfully",
#                         }
#                     ),
#                     200,
#                 )
#             else:
#                 return jsonify({"error": "Invalid verification code"}), 400

#         except Exception as e:
#             return (
#                 jsonify({"error": str(e), "message": "Email verification failed"}),
#                 400,
#             )
