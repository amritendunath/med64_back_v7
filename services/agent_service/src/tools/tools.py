from models.tools import DateModel, DateTimeModel, IdentificationNumberModel
from langchain_core.tools import tool
import pandas as pd
from datetime import datetime
from utils.database import db
import logging, re, os, requests
from service.hospital_search import HospitalLocator
from typing import Dict, Any, Optional, List, Literal
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi import FastAPI, HTTPException, Header, Query
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
from langchain_core.runnables import RunnableConfig
from fastapi import APIRouter, Depends
from models.generate_answer import GenerationResponse, GenerationRequest, ErrorResponse
import contextvars

ehr_id_var = contextvars.ContextVar("ehr_id")

router = APIRouter()
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY not set in environment")

ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

def convert_datetime_format(dt_str):
    # Parse the input datetime string
    dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")

    # Format the output as 'DD-MM-YYYY H.M' (removing leading zero from hour only)
    return dt.strftime("%d-%m-%Y %#H.%M")


async def get_current_user_id(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        ehr_id: str = payload.get("user_ehr_id")
        if ehr_id and ehr_id is None:
            raise credentials_exception

        return ehr_id
    except JWTError:
        raise credentials_exception


# async def get_user_info_tool(input: str, config: RunnableConfig = None) -> str:

# @tool
# def get_user_info_tool(request: Optional[str] = None) -> dict:
#     """Returns the current user's ID."""
#     logger.info("[TOOL INVOKED] get_user_info_tool")
#     return {'message': 'Your user ID is available.', 'data': f"Your user ID is: 007"}


@tool
def get_user_info(user_id: str, email: str) -> str:
    """Return the current user's ID and email."""
    return f"Your ID is {user_id} and your email is {email}."

    # user_id = ehr_id_var.get()
    # if user_id:
    #     return {'message': 'Your user ID is available.', 'data': f"Your user ID is: {user_id}"}
    # return {'message': 'User info not available.', 'data': 'User info not available.'}

    # print("[TOOL INVOKED] get_user_info_tool")
    # user_id = ehr_id_var.get(default=None)
    # if user_id:
    #     return f"Your user ID is: {user_id}"
    # return "User info not available."

    # print("[TOOL INVOKED] get_user_info_tool")
    # if config and config.configurable:
    #     user_email = config.configurable.get("user_email", "unknown")
    #     user_id = config.configurable.get("current_user", "unknown")
    #     return f"Your email is {user_email} and your ID is {user_id}."
    # return "User info not available."




# @router.post("/generate-stream/", response_model=GenerationResponse, responses={500: {"model": ErrorResponse}})
# async def book_appointent(query_date: str, doctor_name: str, hospital_name: str) -> str:
#     try:
#         current_user: str = Depends(get_current_user_id)
#         patient_to_attend = current_user
#         logger.info(f"patient_id_number:{patient_to_attend}")
#         # Format the API URL
#         base_url = "http://127.0.0.1:7001"
#         endpoint = f"/booking"
#         api_url = base_url + endpoint

#         params = {
#             'query_date': query_date,
#             'doctor_name': doctor_name,
#             'hospital_name': hospital_name,
#             'patient_to_attend': patient_to_attend
#         }

#         # Make GET request to the API
#         response = requests.post(api_url, params=params)

#         # Check if request was successful
#         response.raise_for_status()

#         # Parse the response
#         data = response.json()
#         return data

#     except requests.exceptions.RequestException as e:
#         return f"Error checking availability: {str(e)}"



@tool
def check_availability_by_doctor(
        query_date: str,
        doctor_name: str,
        hospital_name: str,
        # config: RunnableConfig = None
    ) -> dict:
    """
    Checking the database if we have availability for the specific doctor.
    The parameters should be mentioned by the user in the query
    """
    try:

        # Format the API URL
        # logger.info(f"token:{token}")
        base_url = "http://localhost:7001"
        endpoint = f"/availability"
        api_url = base_url + endpoint
        # user_email = config.configurable.get("user_email") if config else None
        # ehr_id = config.configurable.get("current_user")

        # logger.info(f"[Tool:check_availability_by_doctor] Checking availability for {doctor_name} on {query_date} at {hospital_name}")
        # logger.debug(f"[Tool] user_email={user_email}, ehr_id={ehr_id}")

        params = {
            'query_date': query_date,
            'doctor_name': doctor_name,
            'hospital_name': hospital_name,
            # 'id':ehr_id
            # 'email': user_email
        }
        # headers = {
        #     'Authorization':
        #     f'Bearer {token}'  # Include the token in the Authorization header
        # }
        # Make GET request to the API
        response = requests.get(api_url, params=params)
        # Check if request was successful
        response.raise_for_status()
        # Parse the response
        data = response.json()
        available_slots = [
            item['date_slot'].split(' ')[1] for item in data.get("data", [])
        ]
        if not available_slots:
            output = "No availability in the entire day"
        else:
            output = f'This availability for {query_date}\n'
            output += "Available slots: " + ', '.join(available_slots)
        return {'message': data.get('message'), 'data': output}
    except requests.exceptions.RequestException as e:
        return f"Error checking availability: {str(e)}"

# @tool
# async def check_availability_by_doctor(
#         query_date: str,
#         doctor_name: str,
#         hospital_name: str,
#         config: RunnableConfig = None
#     ) -> dict:
#     """
#     Checking the database if we have availability for the specific doctor.
#     The parameters should be mentioned by the user in the query
#     """
#     try:

#         # Format the API URL
#         # logger.info(f"token:{token}")
#         base_url = "http://localhost:7001"
#         endpoint = f"/availability"
#         api_url = base_url + endpoint
#         user_email = config.configurable.get("user_email") if config else None
#         ehr_id = config.configurable.get("current_user") if config else None

#         logger.info(f"[Tool:check_availability_by_doctor] Checking availability for {doctor_name} on {query_date} at {hospital_name}")
#         logger.debug(f"[Tool] user_email={user_email}, ehr_id={ehr_id}")

#         params = {
#             'query_date': query_date,
#             'doctor_name': doctor_name,
#             'hospital_name': hospital_name,
#             'id':ehr_id,
#             'email': user_email
#         }
#         # headers = {
#         #     'Authorization':
#         #     f'Bearer {token}'  # Include the token in the Authorization header
#         # }
#         # Make GET request to the API
#         response = requests.get(api_url, params=params)
#         # Check if request was successful
#         response.raise_for_status()
#         # Parse the response
#         data = response.json()
#         available_slots = [
#             item['date_slot'].split(' ')[1] for item in data.get("data", [])
#         ]
#         if not available_slots:
#             output = "No availability in the entire day"
#         else:
#             output = f'This availability for {query_date}\n'
#             output += "Available slots: " + ', '.join(available_slots)
#         return {'message': data.get('message'), 'data': output}
#     except requests.exceptions.RequestException as e:
#         return f"Error checking availability: {str(e)}"


@tool
def check_availability_by_specialization(
    desired_date: DateModel,
    specialization: str
    ):
    """
    Checking the database if we have availability for the specific specialization.
    The parameters should be mentioned by the user in the query
    """
    # Dummy data
    # df = pd.read_csv(f"availability.csv")
    csv_path = os.path.join(os.path.dirname(__file__), "availability.csv")
    df = pd.read_csv(csv_path)

    df["date_slot_time"] = df["date_slot"].apply(lambda input: input.split(" ")[-1])
    rows = (
        df[
            (df["date_slot"].apply(lambda input: input.split(" ")[0])== desired_date.date) &
            (df["specialization"] == specialization) &
            (df["is_available"] == True)
        ]
        .groupby(["specialization", "doctor_name"])["date_slot_time"]
        .apply(list)
        .reset_index(name="available_slots")
    )

    if len(rows) == 0:
        output = "No availability in the entire day"
    else:

        def convert_to_am_pm(time_str):
            # Split the time string into hours and minutes
            time_str = str(time_str)
            hours, minutes = map(int, time_str.split("."))

            # Determine AM or PM
            period = "AM" if hours < 12 else "PM"

            # Convert hours to 12-hour format
            hours = hours % 12 or 12

            # Format the output
            return f"{hours}:{minutes:02d} {period}"

        output = f"This availability for {desired_date.date}\n"
        for row in rows.values:
            output += (
                row[1]
                + ". Available slots: \n"
                + ", \n".join([convert_to_am_pm(value) for value in row[2]])
                + "\n"
            )
    return output


@tool
async def cancel_appointment(query_date: str, doctor_name: str, hospital_name: str, current_user: str):
    """
    Canceling an appointment.
    The parameters MUST be mentioned by the user in the query.
    
    [Args]: patient_to_attend(str) is acting like id_number
    """
    try:
        patient_to_attend = current_user
        # Format the API URL
        base_url = "http://localhost:7001"
        endpoint = f"/cancel"
        api_url = base_url + endpoint

        params = {
            'query_date': query_date,
            'doctor_name': doctor_name,
            'hospital_name': hospital_name,
            'patient_to_attend': patient_to_attend
        }
        # Make GET request to the API
        response = requests.post(api_url, params=params)
        # Check if request was successful
        response.raise_for_status()
        # Parse the response
        data = response.json()
        return data

    except requests.exceptions.RequestException as e:
        return f"Error checking availability: {str(e)}"



@tool
async def set_appointment(
    query_date: str,
    doctor_name: str,
    hospital_name: str,
    # config: RunnableConfig = None  # Catch config from LangChain
) -> str:
    """Book appointment with selected doctor."""

    try:
        # Extract current_user from the config
        # current_user = None
        # if config and hasattr(config, "configurable"):
        #     current_user = config.configurable.get("current_user")

        # logger.info(f"[DEBUG] Tool received current_user: {current_user}")

        # if not current_user:
        #     return "Error: current_user (EHR ID) is missing. Cannot book appointment."
        patient_to_attend = ehr_id_var.get()

        # Compose booking request
        api_url = "http://127.0.0.1:7001/booking"
        params = {
            'query_date': query_date,
            'doctor_name': doctor_name,
            'hospital_name': hospital_name,
            'patient_to_attend': patient_to_attend
        }

        response = requests.post(api_url, params=params)
        response.raise_for_status()

        data = response.json()
        return f"✅ Appointment booked: {data}"

    except requests.exceptions.RequestException as e:
        logger.error(f"[ERROR] Failed to book appointment: {e}")
        return f"❌ Error booking appointment: {str(e)}"

@tool
def reschedule_appointment(
    old_date: DateTimeModel,
    new_date: DateTimeModel,
    id_number: IdentificationNumberModel,
    doctor_name: str,
):
    """
    Rescheduling an appointment.
    The parameters MUST be mentioned by the user in the query.
    """
    df = pd.read_csv(f"availability.csv")
    available_for_desired_date = df[
        (df["date_slot"] == convert_datetime_format(new_date.date))
        & (df["is_available"] == True)
        & (df["doctor_name"] == doctor_name)
    ]
    if len(available_for_desired_date) == 0:
        return "Not available slots in the desired period"
    else:
        cancel_appointment.invoke(
            {"date": old_date, "id_number": id_number, "doctor_name": doctor_name}
        )
        set_appointment.invoke(
            {
                "desired_date": new_date,
                "id_number": id_number,
                "doctor_name": doctor_name,
            }
        )
        return "Succesfully rescheduled for the desired time"

@tool
def find_nearby_hospital(zipcode: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Find and return information about nearby hospitals based on current location or zipcode.

    Args:
        zipcode (Optional[str]): The ZIP code to search for hospitals. If not provided,
                                uses current location.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries containing hospital information including:
            - hospital_info:
                - name: Name of the hospital
                - location: Dictionary containing latitude and longitude
                - distance: Distance from current location in meters
    """
    try:
        locator = HospitalLocator()
        print("HospitalLocator initialized successfully")  # Debug log

        # Simply pass the zipcode (or None) to search_hospitals
        # It will handle the location logic internally
        result = (
            locator.search_hospitals(zipcode)
            if zipcode
            else locator.handle_hospital_query()
        )
        print(f"Result from search_hospitals: {result}")  # Debug log
        if not result:
            return [{"error": "No hospitals found in the specified area"}]
        hospital_lines = [
            f"{i+1}. {h['hospital_info']['name']} ({h['hospital_info']['distance']/1000:.1f} km)"
            for i, h in enumerate(result)
        ]
        response = "Here are the nearby hospitals:\n" + "\n".join(hospital_lines)
        return result
    except Exception as e:
        print(f"Error in find_nearby_hospital: {str(e)}")  # Debug log
        raise ValueError(f"Failed to locate nearby hospitals: {str(e)}")


@tool
def get_doctor_info_by_hospital_name(hospital_name: str) -> List[Dict[str, Any]]:
    """
    Get information about doctors at a specific hospital.

    Args:
        name (str): The name of the hospital to search for doctors.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries containing doctor information.
    """
    try:
        # Format the API URL
        base_url = "http://127.0.0.1:7001"
        endpoint = f"/doctor"
        api_url = base_url + endpoint
        params = {
            'hospital_name': hospital_name.lower()
        }
        # Make GET request to the API
        response = requests.get(api_url, params=params)
        # Check if request was successful
        response.raise_for_status()
        # Parse the response
        data = response.json()
        return data

    except requests.exceptions.RequestException as e:
        return f"Error checking availability: {str(e)}"
