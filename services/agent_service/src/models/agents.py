from models.tools import DateModel, DateTimeModel, IdentificationNumberModel
from langchain_core.pydantic_v1 import constr, BaseModel, Field, validator
from typing import Optional


# Primary Assistant
class ToPrimaryBookingAssistant(BaseModel):
    """Transfers work to a specialized assistant to handle flight updates and cancellations.""",

    request: str = Field(
        description="Any necessary followup questions the update flight assistant should clarify before proceeding.",
        type="string",
    )


class ToGetInfo(BaseModel):
    """Get information of doctor availability via name or specialization"""

    desired_date: DateModel = Field(
        description="The desired date for booking", type="string", format="date"
    )
    doctor_name: Optional[str] = Field(
        default=None, description="The desired doctor name for booking", type="string"
    )
    hospital_name: str = Field(
        default=None,
        description="The name of the hospital where the appointment is to be booked",
        type="string",
    )
    specialization: Optional[str] = Field(
        default=None,
        description="The desired specialization of the doctor",
        type="string",
    )
    request: str = Field(
        default=None,
        description="Any additional information or requests from the user regarding the appointment.",
        type="string",
    )


class ToAppointmentBookingAssistant(BaseModel):
    """Transfer work to a specialized assistant to handle appointment bookings."""

    step: str = Field(
        description="The current step in the booking process (hospital_selection, doctor_selection, appointment_details)",
        type="string",
    )
    hospital_name: Optional[str] = Field(
        default=None, description="The selected hospital name", type="string"
    )
    date: Optional[DateTimeModel] = Field(
        default=None,
        description="The date for setting, cancel or rescheduling appointment",
        type="string",
        format="date-time",
    )
    identification_number: Optional[IdentificationNumberModel] = Field(
        default=None, description="The id number of user.", type="string"
    )
    doctor_name: Optional[str] = Field(
        default=None, description="The name of the doctor", type="string"
    )
    request: str = Field(
        description="Any additional information or requests from the user regarding the appointment booking.",
        type="string",
    )


class CompleteOrEscalate(BaseModel):
    """A tool to mark the current task as completed and/or to escalate control of the dialog to the main assistant,
    who can re-route the dialog based on the user's needs."""

    cancel: bool = Field(default=True, type="boolean")
    reason: str = Field(
        description="The reason for canceling or completing the current task.",
        type="string",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "cancel": True,
                "reason": "User changed their mind about the current task.",
            },
            "example 2": {
                "cancel": True,
                "reason": "I have fully completed the task.",
            },
            "example 3": {
                "cancel": False,
                "reason": "I need to search the user's date and time for more information.",
            },
        }


class ToMedicalAssistant(BaseModel):
    """Transfers work to a specialized assistant to handle medical queries."""

    query: str = Field(description="The medical question or query from the user")
    context: Optional[str] = Field(
        default=None, description="Any additional context about the medical query"
    )


class ToHospitalSearchAssistant(BaseModel):
    query: str = Field(
        description="The nearby hospital question or query from the user", type="string"
    )
    context: Optional[str] = Field(
        default=None, description="Any additional context about the hospital query"
    )
