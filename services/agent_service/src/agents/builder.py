import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph
from agents.AgentState import State
from agents.base import Assistant
from langgraph.graph import START, END
from utils.helper import create_entry_node
from langchain_openai import AzureChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv
from agents.agents import get_runnable
from models.agents import CompleteOrEscalate
from langchain_core.messages import AIMessage, HumanMessage



from utils.prompts import (
    info_agent_prompt,
    primary_agent_prompt,
    medical_agent_prompt,
    booking_agent_prompt,
    hospital_agent_prompt,
)
from models.agents import (
    ToAppointmentBookingAssistant,
    ToGetInfo,
    ToPrimaryBookingAssistant,
    ToMedicalAssistant,
    ToHospitalSearchAssistant,
)

from tools.tools import (
    set_appointment,
    reschedule_appointment,
    cancel_appointment,
    check_availability_by_specialization,
    check_availability_by_doctor,
    find_nearby_hospital,
    get_doctor_info_by_hospital_name,
)
from utils.helper import (
    create_tool_node_with_fallback,
    pop_dialog_state,
    RouteUpdater,
    route_to_workflow,
    route_primary_assistant,
)
from utils.config import get_settings
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3

conn = sqlite3.connect("checkpoints.db", check_same_thread=False)

memory = SqliteSaver(conn)

Azure_Creds = get_settings()

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = Azure_Creds.LANGCHAIN_ENDPOINT
os.environ["LANGCHAIN_API_KEY"] = Azure_Creds.LANGCHAIN_API_KEY
os.environ["LANGCHAIN_PROJECT"] = Azure_Creds.LANGCHAIN_PROJECT


# llm = AzureChatOpenAI(temperature=0,
#                            api_key=Azure_Creds.AZURE_OPENAI_API_KEY,
#                            azure_endpoint=Azure_Creds.AZURE_OPENAI_ENDPOINT,
#                            openai_api_version=Azure_Creds.AZURE_OPENAI_VERSION,
#                            azure_deployment=Azure_Creds.AZURE_GPT4O_MODEL
#                            )
Config = get_settings()
llm = ChatGoogleGenerativeAI(
    model=Config.GEMINI_MODEL,
    google_api_key=Config.GOOGLE_API_KEY,
    temperature=0,
    convert_system_message_to_human=True,  # Add this line
)

info_tools = [
    check_availability_by_specialization,
    check_availability_by_doctor
    
]
info_runnable = get_runnable(
    llm=llm, tools=info_tools + [CompleteOrEscalate], agent_prompt=info_agent_prompt
)

booking_tools = [
    set_appointment,
    reschedule_appointment,
    cancel_appointment,
]

booking_runnable = get_runnable(
    llm=llm,
    tools=booking_tools + [CompleteOrEscalate],
    agent_prompt=booking_agent_prompt,
)

primary_tools = [
    ToHospitalSearchAssistant,
    ToMedicalAssistant,  # Add this first in the list
    ToAppointmentBookingAssistant,
    ToGetInfo,
    ToPrimaryBookingAssistant,
    CompleteOrEscalate,
]
primary_runnable = get_runnable(
    llm=llm, tools=primary_tools, agent_prompt=primary_agent_prompt
)

medical_runnable = get_runnable(
    llm=llm,
    tools=[ToAppointmentBookingAssistant] + [CompleteOrEscalate],
    agent_prompt=medical_agent_prompt,
)

hospital_tools = [
    find_nearby_hospital,
    get_doctor_info_by_hospital_name,
]  # Add CompleteOrEscalate to the tools list

hospital_runnable = get_runnable(
    llm=llm,
    tools=hospital_tools + [CompleteOrEscalate],
    agent_prompt=hospital_agent_prompt,
)


def build_graph() -> StateGraph:
    """
    Builds and returns a state graph for the multi-agent conversation system.

    Returns:
        StateGraph: Compiled state graph with all nodes and edges
    """
    builder = StateGraph(State)

    # Section 1: Core Assistant Nodes
    builder.add_node("primary_assistant", Assistant(primary_runnable))
    builder.add_node("medical_info", Assistant(medical_runnable))
    builder.add_node("get_info", Assistant(info_runnable))
    builder.add_node("appointment_info", Assistant(booking_runnable))
    builder.add_node("hospital_info", Assistant(hospital_runnable))

    # Section 2: Entry Point Nodes
    builder.add_node(
        "enter_medical_info", create_entry_node("Medical Assistant", "medical_info")
    )
    builder.add_node(
        "enter_hospital_info", create_entry_node("Hospital Assistant", "hospital_info")
    )
    builder.add_node(
        "enter_get_info", create_entry_node("Get Information Assistant", "get_info")
    )
    builder.add_node(
        "enter_appointment_info",
        create_entry_node("Appointment Assistant", "appointment_info"),
    )

    # Section 3: Tool Management Nodes
    builder.add_node("update_info_tools", create_tool_node_with_fallback(info_tools))
    builder.add_node(
        "update_appointment_tools", create_tool_node_with_fallback(booking_tools)
    )
    builder.add_node(
        "update_hospital_tools", create_tool_node_with_fallback(hospital_tools)
    )
    builder.add_node("leave_skill", pop_dialog_state)

    # Section 4: Primary Flow Edges
    builder.add_conditional_edges(START, route_to_workflow)
    builder.add_conditional_edges(
        "primary_assistant",
        route_primary_assistant,
        [
            "enter_appointment_info",
            "enter_get_info",
            "enter_medical_info",
            "enter_hospital_info",
            END,
        ],
    )

    # Section 5: Information Flow Edges
    builder.add_edge("enter_get_info", "get_info")
    builder.add_edge("update_info_tools", "get_info")
    builder.add_conditional_edges(
        "get_info",
        RouteUpdater(info_tools, "update_info_tools").route_update_info,
        ["update_info_tools", "leave_skill", END],
    )

    # Section 6: Appointment Flow Edges
    builder.add_edge("enter_appointment_info", "appointment_info")
    builder.add_edge("update_appointment_tools", "appointment_info")
    builder.add_conditional_edges(
        "appointment_info",
        RouteUpdater(booking_tools, "update_appointment_tools").route_update_info,
        ["update_appointment_tools", "leave_skill", END],
    )

    # Section 7: Medical Flow Edges
    builder.add_edge("enter_medical_info", "medical_info")
    builder.add_conditional_edges(
        "medical_info",
        RouteUpdater(
            [ToAppointmentBookingAssistant, CompleteOrEscalate], None
        ).route_update_info,
        ["primary_assistant", "leave_skill", END],
    )
    # Section 8: Hospital Flow Edges
    builder.add_edge("enter_hospital_info", "hospital_info")
    builder.add_edge("update_hospital_tools", "hospital_info")
    builder.add_conditional_edges(
        "hospital_info",
        RouteUpdater(hospital_tools, "update_hospital_tools").route_update_info,
        ["update_hospital_tools", "leave_skill", END],
    )

    # Section 8: Return Path Edges
    builder.add_edge("leave_skill", "primary_assistant")

    # Compile and Return Graph
    graph = builder.compile(checkpointer=memory)
    return graph

