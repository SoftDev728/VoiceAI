import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Config:
    """Application configuration settings"""

    # OpenAI Configuration
    OPENAI_API_KEY: str = os.environ["OPENAI_API_KEY"]  # Will raise error if missing

    # Google Sheets Configuration
    GOOGLE_SHEETS_URL: str = os.environ["GOOGLE_SHEETS_URL"]
    CREDENTIALS_FILE: str = os.environ["CREDENTIALS_FILE"]

    # Google Sheets Scopes
    GOOGLE_SCOPES = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive"
    ]

    # Hospital Information
    HOSPITAL_NAME: str = os.environ["HOSPITAL_NAME"]
    HOSPITAL_ADDRESS: str = os.environ["HOSPITAL_ADDRESS"]
    HOSPITAL_PHONE: str = os.environ["HOSPITAL_PHONE"]
    OPD_HOURS: str = os.environ["OPD_HOURS"]

    # Sheet Headers
    APPOINTMENT_HEADERS = [
        "Appointment ID",
        "Patient Name",
        "Problem",
        "Appointment Date",
        "Appointment Time",
        "Booking Timestamp",
        "Status"
    ]

    # LLM Configuration
    LLM_MODEL_PROVIDER: str = os.environ["LLM_MODEL_PROVIDER"]
    LLM_MODEL: str = os.environ["LLM_MODEL"]
    TTS_MODEL: str = os.environ["TTS_MODEL"]
    TTS_VOICE: str = os.environ["TTS_VOICE"]
    STT_MODEL: str = os.environ["STT_MODEL"]
