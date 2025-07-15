from pydantic_settings import BaseSettings
from functools import lru_cache
import os

class Settings(BaseSettings):
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL")
    LANGCHAIN_ENDPOINT: str = os.getenv("LANGCHAIN_ENDPOINT")
    LANGCHAIN_API_KEY: str = os.getenv("LANGCHAIN_API_KEY")
    LANGCHAIN_PROJECT: str = os.getenv("LANGCHAIN_PROJECT")
    AI_SEARCH_KEY: str = os.getenv("AI_SEARCH_KEY")
    AI_SEARCH_ENDPOINT: str = os.getenv("AI_SEARCH_ENDPOINT")
    AI_SEARCH_INDEX: str = os.getenv("AI_SEARCH_INDEX")
    AI_SEARCH_VECTOR_SIZE: int = int(os.getenv("AI_SEARCH_VECTOR_SIZE", "1536"))
    AI_SEARCH_K: int = int(os.getenv("AI_SEARCH_K", "4"))
    AI_SEARCH_SCORE_THRESHOLD: float = float(os.getenv("AI_SEARCH_SCORE_THRESHOLD", "0.8"))
    AI_SEARCH_TOP_K: int = int(os.getenv("AI_SEARCH_TOP_K", "10"))
    AI_SEARCH_TOP_P: float = float(os.getenv("AI_SEARCH_TOP_P", "0.9"))
    AI_SEARCH_MAX_TOKENS: int = int(os.getenv("AI_SEARCH_MAX_TOKENS", "500"))
    AI_SEARCH_TEMPERATURE: float = float(os.getenv("AI_SEARCH_TEMPERATURE", "0.7"))
    AI_SEARCH_FREQUENCY_PENALTY: float = float(os.getenv("AI_SEARCH_FREQUENCY_PENALTY", "0.0"))
    AI_SEARCH_PRESENCE_PENALTY: float = float(os.getenv("AI_SEARCH_PRESENCE_PENALTY", "0.0"))
    AI_SEARCH_STOP: list = os.getenv("AI_SEARCH_STOP", "").split(",")
    AI_SEARCH_STREAM: bool = os.getenv("AI_SEARCH_STREAM", "False").lower() == "true"
    AI_SEARCH_VERBOSE: bool = os.getenv("AI_SEARCH_VERBOSE", "False").lower() == "true"
    AI_SEARCH_ENGINE: str = os.getenv("AI_SEARCH_ENGINE")
    AI_SEARCH_PROMPT: str = os.getenv("AI_SEARCH_PROMPT")
    AI_SEARCH_PROMPT_TEMPLATE: str = os.getenv("AI_SEARCH_PROMPT_TEMPLATE")
    AI_SEARCH_PROMPT_PREFIX: str = os.getenv("AI_SEARCH_PROMPT_PREFIX")
    AI_SEARCH_PROMPT_SUFFIX: str = os.getenv("AI_SEARCH_PROMPT_SUFFIX")
    AI_SEARCH_PROMPT_INPUT_VARIABLES: list = os.getenv("AI_SEARCH_PROMPT_INPUT_VARIABLES", "").split(",")
    AI_SEARCH_PROMPT_OUTPUT_PARSER: str = os.getenv("AI_SEARCH_PROMPT_OUTPUT_PARSER")
    AI_SEARCH_PROMPT_MEMORY: str = os.getenv("AI_SEARCH_PROMPT_MEMORY")
    AI_SEARCH_PROMPT_CHAT_HISTORY: str = os.getenv("AI_SEARCH_PROMPT_CHAT_HISTORY")
    AI_SEARCH_PROMPT_CHAT_MESSAGE_HISTORY: str = os.getenv("AI_SEARCH_PROMPT_CHAT_MESSAGE_HISTORY")
    AI_SEARCH_PROMPT_CHAT_MESSAGE_HISTORY_INPUT_KEY: str = os.getenv("AI_SEARCH_PROMPT_CHAT_MESSAGE_HISTORY_INPUT_KEY")
    AI_SEARCH_PROMPT_CHAT_MESSAGE_HISTORY_OUTPUT_KEY: str = os.getenv("AI_SEARCH_PROMPT_CHAT_MESSAGE_HISTORY_OUTPUT_KEY")
    AI_SEARCH_PROMPT_CHAT_MESSAGE_HISTORY_OUTPUT_PARSER: str = os.getenv("AI_SEARCH_PROMPT_CHAT_MESSAGE_HISTORY_OUTPUT_PARSER")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


# from pydantic_settings import BaseSettings
# from functools import lru_cache
# import yaml
# import os



# with open("devConfig.yaml") as f:
#     configParser = yaml.load(f, Loader=yaml.SafeLoader)


# # class Settings(BaseSettings):
# #     AZURE_OPENAI_API_KEY: str =  configParser['AZURE_OPENAI_API_KEY']
# #     AZURE_OPENAI_ENDPOINT: str =  configParser['AZURE_OPENAI_ENDPOINT']
# #     AZURE_OPENAI_VERSION: str =  configParser['AZURE_OPENAI_VERSION']
# #     AZURE_GPT4O_MODEL: str =  configParser['AZURE_GPT4O_MODEL']
# #     AZURE_OPENAI_EMBEDDINGS_MODEL: str =  configParser['AZURE_OPENAI_EMBEDDINGS_MODEL']
# #     LANGCHAIN_ENDPOINT: str =  configParser['LANGCHAIN_ENDPOINT']
# #     LANGCHAIN_API_KEY: str =  configParser['LANGCHAIN_API_KEY']
# #     LANGCHAIN_PROJECT: str =  configParser['LANGCHAIN_PROJECT']
# #     AI_SEARCH_KEY: str =  configParser['AI_SEARCH_KEY']
# #     AI_SEARCH_ENDPOINT: str =  configParser['AI_SEARCH_ENDPOINT']


# class Settings(BaseSettings):
#     GOOGLE_API_KEY: str = configParser["GOOGLE_API_KEY"]
#     GEMINI_MODEL: str = configParser["GEMINI_MODEL"]
#     LANGCHAIN_ENDPOINT: str = configParser["LANGCHAIN_ENDPOINT"]
#     LANGCHAIN_API_KEY: str = configParser["LANGCHAIN_API_KEY"]
#     LANGCHAIN_PROJECT: str = configParser["LANGCHAIN_PROJECT"]
#     AI_SEARCH_KEY: str = configParser["AI_SEARCH_KEY"]
#     AI_SEARCH_ENDPOINT: str = configParser["AI_SEARCH_ENDPOINT"]
#     AI_SEARCH_INDEX: str = configParser["AI_SEARCH_INDEX"]
#     AI_SEARCH_VECTOR_SIZE: int = configParser["AI_SEARCH_VECTOR_SIZE"]
#     AI_SEARCH_K: int = configParser["AI_SEARCH_K"]
#     AI_SEARCH_SCORE_THRESHOLD: float = configParser["AI_SEARCH_SCORE_THRESHOLD"]
#     AI_SEARCH_TOP_K: int = configParser["AI_SEARCH_TOP_K"]
#     AI_SEARCH_TOP_P: float = configParser["AI_SEARCH_TOP_P"]
#     AI_SEARCH_MAX_TOKENS: int = configParser["AI_SEARCH_MAX_TOKENS"]
#     AI_SEARCH_TEMPERATURE: float = configParser["AI_SEARCH_TEMPERATURE"]
#     AI_SEARCH_FREQUENCY_PENALTY: float = configParser["AI_SEARCH_FREQUENCY_PENALTY"]
#     AI_SEARCH_PRESENCE_PENALTY: float = configParser["AI_SEARCH_PRESENCE_PENALTY"]
#     AI_SEARCH_STOP: list = configParser["AI_SEARCH_STOP"]
#     AI_SEARCH_STREAM: bool = configParser["AI_SEARCH_STREAM"]
#     AI_SEARCH_VERBOSE: bool = configParser["AI_SEARCH_VERBOSE"]
#     AI_SEARCH_ENGINE: str = configParser["AI_SEARCH_ENGINE"]
#     AI_SEARCH_PROMPT: str = configParser["AI_SEARCH_PROMPT"]
#     AI_SEARCH_PROMPT_TEMPLATE: str = configParser["AI_SEARCH_PROMPT_TEMPLATE"]
#     AI_SEARCH_PROMPT_PREFIX: str = configParser["AI_SEARCH_PROMPT_PREFIX"]
#     AI_SEARCH_PROMPT_SUFFIX: str = configParser["AI_SEARCH_PROMPT_SUFFIX"]
#     AI_SEARCH_PROMPT_INPUT_VARIABLES: list = configParser[
#         "AI_SEARCH_PROMPT_INPUT_VARIABLES"
#     ]
#     AI_SEARCH_PROMPT_OUTPUT_PARSER: str = configParser["AI_SEARCH_PROMPT_OUTPUT_PARSER"]
#     AI_SEARCH_PROMPT_MEMORY: str = configParser["AI_SEARCH_PROMPT_MEMORY"]
#     AI_SEARCH_PROMPT_CHAT_HISTORY: str = configParser["AI_SEARCH_PROMPT_CHAT_HISTORY"]
#     AI_SEARCH_PROMPT_CHAT_MESSAGE_HISTORY: str = configParser[
#         "AI_SEARCH_PROMPT_CHAT_MESSAGE_HISTORY"
#     ]
#     AI_SEARCH_PROMPT_CHAT_MESSAGE_HISTORY_INPUT_KEY: str = configParser[
#         "AI_SEARCH_PROMPT_CHAT_MESSAGE_HISTORY_INPUT_KEY"
#     ]
#     AI_SEARCH_PROMPT_CHAT_MESSAGE_HISTORY_OUTPUT_KEY: str = configParser[
#         "AI_SEARCH_PROMPT_CHAT_MESSAGE_HISTORY_OUTPUT_KEY"
#     ]
#     AI_SEARCH_PROMPT_CHAT_MESSAGE_HISTORY_OUTPUT_PARSER: str = configParser[
#         "AI_SEARCH_PROMPT_CHAT_MESSAGE_HISTORY_OUTPUT_PARSER"
#     ]


# @lru_cache(maxsize=1)
# def get_settings() -> Settings:
#     return Settings()
