# import os
# import sys
# import re

# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# from flask import request, jsonify
# from twilio.base.exceptions import TwilioRestException
# from werkzeug.exceptions import BadRequest
# from twilio.rest import Client
# from flask_jwt_extended import create_access_token

# from utils.database import Database
# from utils.helpers import RouteUpdater
# import logging
# import boto3
# import os
# import logging
# from botocore.exceptions import ClientError
# from dotenv import load_dotenv

# load_dotenv()


# class PhoneAuth:

#     def __init__(self):
#         """
#         Initialize the service with a Redis connection, a logger, and an SNS client.

#         Args:
#             r (redis.Redis): Redis client instance.
#             logger (logging.Logger): Logger instance.
#             sns_client (boto3.client): SNS client instance.
#         """
#         self.sns_client = boto3.client(
#             "sns",
#             aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
#             aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
#             region_name=os.getenv("AWS_REGION"),
#         )
#         self.helper = RouteUpdater()
#         self.logger = logging.getLogger(__name__)



#     def send_otp_to_phone(self, phone_number: str) -> dict:
#         """
#         Send OTP via Amazon SNS to the specified phone number

#         Args:
#             phone_number(str): generate a code and send to the phone_number 
#             and saved in the cache
        
#         Returns:
#             dict: A result dictionary with keys 'success' (str) and 'message_id' (str).
#         """
#         # Generate OTP
#         otp = self.helper.store_verification_code(phone_number)

#         # Format phone number to E.164 format (required by SNS)
#         # Assuming this is a US number; adjust country code if different
#         if not phone_number.startswith("+"):
#             phone_number = "+91" + phone_number  # Adding US country code

#         # Create SNS client
#         # Use environment variables or AWS credentials file for authentication
#         try:
#             # Compose message
#             message = f"Your verification code is: {otp}. This code will expire in 10 minutes."

#             # Send SMS
#             response = self.sns_client.publish(
#                 PhoneNumber=phone_number,
#                 Message=message,
#                 MessageAttributes={
#                     "AWS.SNS.SMS.SMSType": {
#                         "DataType": "String",
#                         "StringValue": "Transactional",  # Use 'Transactional' for OTPs (higher priority)
#                     }
#                 },
#             )

#             self.logger.info(
#                 f"OTP sent successfully to {phone_number}. Message ID: {response['MessageId']}"
#             )

#             # In a real application, you would store the OTP securely for verification
#             # For example, in a database with the user's ID, a hash of the OTP, and an expiration timestamp

#             return {
#                 "success": True,
#                 "message_id": response["MessageId"],
#                 "otp": otp,  # In production, don't return the OTP directly
#             }

#         except ClientError as e:
#             error_code = e.response["Error"]["Code"]
#             error_message = e.response["Error"]["Message"]
#             self.logger.error(f"Failed to send OTP: {error_code} - {error_message}")

#             return {"success": False, "error": f"{error_code}: {error_message}"}
#         except Exception as e:
#             self.logger.error(f"Unexpected error: {str(e)}")

#             return {"success": False, "error": str(e)}
    



#     def check_and_verify_phone_number(self, phone_number: str) -> dict:
#         """
#         Check if a phone number is verified in the SNS sandbox.
#         If verified, send otp to the phone number
#         If not, send a verification request.


#         Args:
#             phone_number (str): Phone number to check/verify

#         Returns:
#             dict: Result with status and message
#         """

#         # Ensure phone number is in E.164 format
#         if not phone_number.startswith("+"):
#             if len(phone_number) == 10:  # US number without country code
#                 phone_number = f"+91{phone_number}"
#             else:
#                 phone_number = f"+91{phone_number}"

#         try:
#             # Check if the phone number is already verified
#             verified_numbers = self.sns_client.list_sms_sandbox_phone_numbers()

#             # if verified_numbers:
#             # Check if phone number is in the list of verified numbers
#             for number in verified_numbers.get("PhoneNumbers", []):
#                 if number["PhoneNumber"] == phone_number:
#                     if number["Status"] == "Verified":
#                         sending_otp = self.send_otp_to_phone(phone_number)

#                         return {
#                             "verified": True,
#                             "message": f"Phone number {phone_number} is already verified and OTP has sent",
#                         }
#                     else:
#                         return {
#                             "verified": False,
#                             "pending": True,
#                             "message": f"Phone number {phone_number} is pending verification. Check your phone for the verification code.",
#                         }

#             # If not verified, create a new verification request
#             if phone_number not in verified_numbers:
#                 response = self.sns_client.create_sms_sandbox_phone_number(
#                     PhoneNumber=phone_number, LanguageCode="en-US"
#                 )

#             return {
#                 "verified": False,
#                 "pending": True,
#                 "message": f"Verification request sent to {phone_number}. Check your phone for the verification code.",
#             }
#         except ClientError as e:
#             error_code = e.response["Error"]["Code"]
#             error_message = e.response["Error"]["Message"]

#             return {
#                 "verified": False,
#                 "pending": False,
#                 "error": True,
#                 "message": f"Error: {error_code} - {error_message}",
#             }




#     def resend_verification_code(self, phone_number: str) -> dict:
#         """
#         Resend the verification code to a phone number in the SNS SMS sandbox.

#         Args:
#             phone_number (str): Phone number to resend verification code to

#         Returns:
#             dict: Result with status and message
#         """
#         # Ensure phone number is in E.164 format
#         if not phone_number.startswith("+"):
#             if len(phone_number) == 10:  # US number without country code
#                 phone_number = f"+91{phone_number}"
#             else:
#                 phone_number = f"+91{phone_number}"

#         try:
#             # First, check if the phone number exists in the sandbox
#             verified_numbers = self.sns_client.list_sms_sandbox_phone_numbers()

#             phone_exists = False
#             for number in verified_numbers.get("PhoneNumbers", []):
#                 if number["PhoneNumber"] == phone_number:
#                     phone_exists = True
#                     break

#             # if phone_exists:
#             #     # If the phone exists, delete it first (this is necessary to resend)
#             #     sns_client.delete_sms_sandbox_phone_number(
#             #         PhoneNumber=phone_number
#             #     )

#             # Create a new verification request (this will send a new code)
#             response = self.sns_client.create_sms_sandbox_phone_number(
#                 PhoneNumber=phone_number, LanguageCode="en-US"
#             )

#             return {
#                 "success": True,
#                 "message": f"New verification code sent to {phone_number}. Check your phone for the verification code.",
#             }

#         except ClientError as e:
#             error_code = e.response["Error"]["Code"]
#             error_message = e.response["Error"]["Message"]

#             return {
#                 "success": False,
#                 "error_code": error_code,
#                 "message": f"Error: {error_message}",
#             }
#         except Exception as e:
#             return {"success": False, "message": f"Unexpected error: {str(e)}"}
        
        

#     def verify_sms_sandbox_phone_number(self, phone_number, verification_code):
#         """
#             Verify a phone number in the SNS SMS sandbox using the verification code.

#         Args:
#             phone_number (str): Phone number to verify (will be formatted to E.164)
#             verification_code (str): The verification code received via SMS

#         Returns:
#             dict: Result with status and message
#         """
#         # Ensure phone number is in E.164 format
#         if not phone_number.startswith("+"):
#             if len(phone_number) == 10:  # US number without country code
#                 phone_number = f"+91{phone_number}"
#             else:
#                 phone_number = f"+91{phone_number}"

#         try:
#             # Verify the phone number with the received code
#             response = self.sns_client.verify_sms_sandbox_phone_number(
#                 PhoneNumber=phone_number, OneTimePassword=verification_code
#             )

#             return {
#                 "success": True,
#                 "message": f"Phone number {phone_number} has been successfully verified!",
#             }

#         except ClientError as e:
#             error_code = e.response["Error"]["Code"]
#             error_message = e.response["Error"]["Message"]

#             # Handle specific error cases
#             if error_code == "InvalidParameterException" and "OTP" in error_message:
#                 return {
#                     "success": False,
#                     "error_type": "invalid_code",
#                     "message": "The verification code is incorrect. Please try again.",
#                 }
#             elif error_code == "VerificationException":
#                 return {
#                     "success": False,
#                     "error_type": "verification_failed",
#                     "message": "Verification failed. The code may have expired. Please request a new code.",
#                 }
#             else:
#                 return {
#                     "success": False,
#                     "error_type": "other",
#                     "error_code": error_code,
#                     "message": f"Error: {error_message}",
#                 }
#         except Exception as e:
#             return {
#                 "success": False,
#                 "error_type": "unexpected",
#                 "message": f"Unexpected error: {str(e)}",
#             }




#     def verify_otp(self, phone_number: str, provided_otp: str) -> bool:
#         """
#         Verify the OTP provided by the user

#         Get the code(otp) from the cache for the phone_number 
#         and match with the provided_otp by user
        
#         Args:
#             phone_number(str): The Phone number to verify
#             provided_otp(str): The OTP verification code by user

#             If matched, creates a token and sent to the homepage
#             If not, then return False - means failed

#         Returns:
#             bool: A boolean indicating whether the deletion was successful.
#                 - True: Verification successfully.
#                 - False: Verification unsuccessfull.
#         """

#         stored_otp = self.helper.get_verification_code(phone_number)

#         if provided_otp == stored_otp:
#             self.logger.info(f"OTP verification successful for {phone_number}")
#             return True
#         else:
#             self.logger.warning(f"OTP verification failed for {phone_number}")
#             return False




#     def verify_sms_otp(self, phone_number: str, verification_code: str) -> dict:
#         """
#         Verify an SMS OTP for a given phone number.

#         First, checks if the phone number is in the AWS SNS Sandbox.
#         If it is, uses the sandbox verification method.
#         If it is not, uses the normal verification method.

#         Args:
#             phone_number (str): The phone number to verify.
#             verification_code (str): The OTP verification code.

#         Returns:
#             dict: A result dictionary with keys 'success' (bool) and 'message' (str).
#         """
#         response = self.sns_client.list_sms_sandbox_phone_numbers()
#         verified_phonenumber = [
#             num["PhoneNumber"] for num in response.get("PhoneNumbers", [])
#         ]
#         if phone_number in verified_phonenumber:
#             verify_method_one = self.verify_otp(phone_number, verification_code)
#             return {
#                 "success": True,
#                 "message": f"Verified phone number:{phone_number} successfully: {verify_method_one}",
#             }
#         # if phone_number not in verified_phonenumber:
#         else:
#             verify_method_two = self.verify_sms_sandbox_phone_number(
#                 phone_number, verification_code
#             )
#             return {
#                 "success": True,
#                 "message": f"Verified phone number:{phone_number} successfully: {verify_method_two}",
#             }


# if __name__ == "__main__":
#     cla = PhoneAuth()
#     # result = cla.check_and_verify_phone_number("9339525478")
#     result = cla.send_otp_to_phone("9804395695")
#     print(result)

# from unittest.mock import MagicMock
# class PhoneAuth:
#     def __init__(self):
#         self.twilio_client = Client(
#             os.getenv('TWILIO_ACCOUNT_SID'),
#             os.getenv('TWILIO_AUTH_TOKEN'),
#         )
#         self.service_id = os.getenv('TWILIO_VERIFY_SERVICE_ID')
#         self.db = Database()
#         self.route_updater = RouteUpdater()
#         self.logger = logging.getLogger(__name__)

#     def test(self):
#         # Step 1: Send OTP
#         self.twilio_client.verify.services(self.service_id).verifications.create(
#             to="+919339525478",  # new mobile number
#             channel="sms"        # or 'call', 'email'
#         )

#         # Step 2: Check OTP (after user enters it)
#         code = input("Enter the OTP: ")
#         result = self.twilio_client.verify.services(self.service_id).verification_checks.create(
#         to="+919339525478",
#         code=code
#         )
#         if result.status == "approved":
#             print("✅ Number verified!")
#         else:
#             print("❌ Verification failed.")

#     def send_verification(self):
#         try:
#             # data = request.get_json()
#             # phone_number = data.get('phoneNumber')
#             mock_request = MagicMock()
#             mock_request.get_json.return_value = {"phoneNumber": "+919339525478"}
#             request = mock_request
#             phone_number = request.get_json().get('phoneNumber')

#             verification = self.twilio_client.verify \
#                 .v2 \
#                 .services(self.service_id) \
#                 .verifications \
#                 .create(to=phone_number, channel='sms')
            
#             return jsonify({
#                 "status": verification.status,
#                 "message": f"Verification code sent successfully {verification}"
#             }), 200
#         except TwilioRestException as e:
#             return jsonify({
#                 "error": str(e),
#                 "message": "Failed to send verification code"
#             }), 400

#     def verify_code(self):
#         data = request.get_json()
#         phone_number = data.get('phoneNumber')
#         code = data.get('code')

#         if not phone_number or not code:
#             raise BadRequest("Phone number and code are required.")

#         try:
#             verification_check = self.twilio_client.verify \
#                 .v2 \
#                 .services(self.service_id) \
#                 .verification_checks \
#                 .create(to=phone_number, code=code)
#         except TwilioRestException as e:
#             logging.error(f"Twilio error: {e}")
#             raise BadRequest("Failed to verify phone number.")

#         if verification_check.status == 'approved':
#             if phone_number:  # Ensure phone_number is not None or empty
#                 user = self.db.users.find_one(
#                     {"email": { "$regex": f"^{re.escape(phone_number)}$", "$options": "i" }},
#                 )
#                 logging.info(f"User: {user}")
#                 if not user:
#                     user_ehr_id = self.route_updater.get_next_ehr_id()
#                     new_user = {
#                         'email': phone_number,
#                         'name': data.get('name'),
#                         'picture': data.get('picture'),
#                         'auth_provider': 'phone',
#                         'user_ehr_id': user_ehr_id
#                     }
#                     self.db.insert_user(new_user)

#                 # If user found then use existing user_ehr_id
#                 user_ehr_id = user.get('user_ehr_id')
#                 logging.info(f"User EHR ID: {user_ehr_id}")
#                 # Create JWT token after successful verification
#                 access_token = create_access_token(
#                     identity=phone_number,
#                     additional_claims={
#                         'phone': phone_number,
#                         'auth_provider': 'phone',
#                         'user_ehr_id': user_ehr_id
#                     }
#                 )
#                 logging.info(f"Generated JWT Token: {access_token}")
#                 return jsonify({"access_token": access_token}), 200
#             else:
#                 logging.error("Phone number is missing or invalid.")
#                 raise BadRequest("Phone number is missing or invalid.")
#         else:
#             logging.error("Invalid verification code.")
#             raise BadRequest("Invalid verification code.")

# if __name__ == "__main__":
#     cla = PhoneAuth()
#     send = cla.test()
#     print(send)