from langchain_core.runnables import RunnableConfig
from langchain_core.runnables import RunnableLambda, RunnableMap, RunnableBranch
from langchain_google_genai import ChatGoogleGenerativeAI
from tools.tools import get_user_info
from langchain_core.output_parsers import StrOutputParser


llm = ChatGoogleGenerativeAI(
    model='gemini-2.0-flash-lite' ,
    google_api_key='AIzaSyCP99HXunPMPTWkitdFEzGBFgAXp62mYbg',
    temperature=0,
    convert_system_message_to_human=True,
    )

def build_prompt(x):
    user_input = x["messages"]
    tool_output = x["user_data"]
    return (
        f"You are a helpful assistant.\n"
        f"If the user greets you, respond warmly. If they ask for their ID or email, use the info below.\n\n"
        f"User says: {user_input}\n"
        f"🛠 Tool info: {tool_output}\n"
        f"Respond appropriately."
    )

def create_agent_chain(user_id: str, email: str):
    tool_call_logic = RunnableLambda(
        lambda x: {"user_id": str(user_id), "email": email}
    ) | get_user_info

    hybrid_chain = RunnableMap({
        "messages": lambda x: x["messages"],
        "user_data": tool_call_logic
    }) | RunnableLambda(build_prompt) | llm | StrOutputParser()
    # }) | RunnableLambda(build_prompt) | llm | (lambda x: x.content)

    return hybrid_chain