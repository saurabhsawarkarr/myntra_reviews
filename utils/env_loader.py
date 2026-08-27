import os
from dotenv import load_dotenv

load_dotenv()

def get_env(key: str, required: bool = True) -> str:
    value = os.getenv(key)
    if required and not value:
        raise EnvironmentError(f"Missing required environment variable: {key}")
    return value
