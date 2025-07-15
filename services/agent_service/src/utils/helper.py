from agents.AgentState import State
from models.agents import (
    ToHospitalSearchAssistant,
    CompleteOrEscalate,
    ToAppointmentBookingAssistant,
    ToMedicalAssistant,
    ToGetInfo,
)
from langgraph.prebuilt import tools_condition, ToolNode
from langgraph.graph import END
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableLambda
from typing import Callable, Literal
import re


class RouteUpdater:
    def __init__(self, tools, update_tool):
        self.tools = tools
        self.update_tool = update_tool

    def route_update_info(self, state: State):
        route = tools_condition(state)
        if route == END:
            return END
        tool_calls = state["messages"][-1].tool_calls
        did_cancel = any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls)
        if did_cancel:
            return "leave_skill"
        # Track conversation state to avoid repetition
        message_text = str(state["messages"][-1]).lower()
        if "appointment" in message_text and "booked" in message_text:
            return END  # Appointment successfully booked

        # Check if we're still gathering information
        safe_toolnames = [
            t.name if hasattr(t, "name") else t.__name__ for t in self.tools
        ]
        if all(tc["name"] in safe_toolnames for tc in tool_calls):
            return self.update_tool


def create_entry_node(assistant_name: str, new_dialog_state: str) -> Callable:
    def entry_node(state: State) -> dict:
        tool_call_id = state["messages"][-1].tool_calls[0]["id"]
        return {
            "messages": [
                ToolMessage(
                    content=f"The assistant is now the {assistant_name}. Reflect on the above conversation between the host assistant and the user."
                    f" The user's intent is unsatisfied. Use the provided tools to assist the user. Remember, you are {assistant_name},"
                    " and the booking, update, other other action is not complete until after you have successfully invoked the appropriate tool."
                    " If the user changes their mind or needs help for other tasks, call the CompleteOrEscalate function to let the primary host assistant take control."
                    f" Do not mention who you are - just act as the proxy for the assistant.",
                    tool_call_id=tool_call_id,
                )
            ],
            "dialog_state": new_dialog_state,
        }

    return entry_node


def handle_tool_error(state) -> dict:
    error = state.get("error")
    tool_calls = state["messages"][-1].tool_calls
    return {
        "messages": [
            ToolMessage(
                content=f"Error: {repr(error)}\n please fix your mistakes.",
                tool_call_id=tc["id"],
            )
            for tc in tool_calls
        ]
    }


def create_tool_node_with_fallback(tools: list) -> dict:
    return ToolNode(tools).with_fallbacks(
        [RunnableLambda(handle_tool_error)], exception_key="error"
    )


def pop_dialog_state(state: State) -> dict:
    """Pop the dialog stack and return to the main assistant.

    This lets the full graph explicitly track the dialog flow and delegate control
    to specific sub-graphs.
    """
    messages = []
    if state["messages"][-1].tool_calls:
        # Note: Doesn't currently handle the edge case where the llm performs parallel tool calls
        messages.append(
            ToolMessage(
                content="Resuming dialog with the host assistant. Please reflect on the past conversation and assist the user as needed.",
                tool_call_id=state["messages"][-1].tool_calls[0]["id"],
            )
        )
    return {
        "dialog_state": "pop",
        "messages": messages,
    }


def route_to_workflow(
    state: State,
) -> Literal[
    "primary_assistant", "appointment_info", "get_info", "medical_info", "hospital_info"
]:
    """If we are in a delegated state, route directly to the appropriate assistant."""
    # Print available keys for debugging
    print("Available state keys:", state.keys())

    # Initialize required state keys if they don't exist
    if "hospital_info" not in state:
        state["hospital_info"] = []

    if "dialog_state" not in state:
        state["dialog_state"] = ["primary_assistant"]
        return "primary_assistant"

    # Ensure dialog_state is not empty
    if not state["dialog_state"]:
        state["dialog_state"] = ["primary_assistant"]
        return "primary_assistant"

    return state["dialog_state"][-1]


# def route_to_workflow(
#     state: State,
# ) -> Literal[
#     "primary_assistant",
#     "appointment_info",
#     "get_info",
#     "medical_info",
#     "hospital_info"
# ]:
#     """If we are in a delegated state, route directly to the appropriate assistant."""
#     dialog_state = state.get("dialog_state")
#     if not dialog_state:
#         return "primary_assistant"
#     # elif "hospital_info" not in state:
#     #     state["hospital_info"] = []
#     return dialog_state[-1]


def route_primary_assistant(state: State, ):
    route = tools_condition(state)
    if route == END:
        return END
    tool_calls = state["messages"][-1].tool_calls
    if tool_calls:
        if tool_calls[0]["name"] == ToAppointmentBookingAssistant.__name__:
            # Extract and normalize date/time from the message
            message_text = str(state["messages"][-1]).lower()
            if any(keyword in message_text for keyword in ["my email", "who am i", "my id", "personal info"]):
                return "ToGetInfo"
            # Check for common date/time patterns
            date_patterns = [
                r"\d{4}-\d{2}-\d{2}\s+\d{1,2}:\d{2}",  # YYYY-MM-DD HH:MM
                r"\d{4}-\d{2}-\d{2}\s+at\s+\d{1,2}:\d{2}\s*(?:am|pm)?",  # YYYY-MM-DD at HH:MM AM/PM
                r"\d{2}-\d{2}-\d{4}\s+\d{1,2}[:.]\d{2}",  # DD-MM-YYYY HH.MM or HH:MM
            ]

            has_valid_date = any(
                re.search(pattern, message_text, re.IGNORECASE)
                for pattern in date_patterns)

            # Check for required information
            has_doctor = "doctor" in message_text or "dentist" in message_text
            has_id = bool(re.search(r"\b\d{7}\b",
                                    message_text))  # Check for 7-digit ID

            if has_valid_date and has_doctor and has_id:
                return "enter_appointment_info"
            return "enter_appointment_info"  # Get missing information first
        if tool_calls[0]["name"] == ToMedicalAssistant.__name__:
            return "enter_medical_info"
        if tool_calls[0]["name"] == ToHospitalSearchAssistant.__name__:
            return "enter_hospital_info"
        if tool_calls[0]["name"] == ToGetInfo.__name__:
            return "enter_get_info"
        if tool_calls[0]["name"] == CompleteOrEscalate.__name__:
            return END
    return END
