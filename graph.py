from services.conversation_manager import conversation_manager
from storage.memory_storage import memory_storage
from storage.sheets_manager import sheets_manager
from config import Config
from models import AppointmentData

# Export the main functions for backward compatibility
def process_user_message(user_input: str, user_id: str = "default") -> str:
    """Process user message through the conversation manager"""
    return conversation_manager.process_user_message(user_input, user_id)

def reset_conversation(user_id: str = "default") -> None:
    """Reset conversation for a specific user"""
    conversation_manager.reset_conversation(user_id)

def get_appointments_array():
    """Get appointments as array of objects for frontend display"""
    return memory_storage.get_appointments_list()

def save_appointment_to_google_sheet(appointment_data: dict) -> bool:
    """Save appointment data to Google Sheets (legacy compatibility)"""
    # Convert dict to AppointmentData if needed
    if isinstance(appointment_data, dict):
        appointment = AppointmentData(
            appointment_id=appointment_data.get("appointment_id", ""),
            patient_name=appointment_data.get("patient_name", ""),
            problem=appointment_data.get("problem", ""),
            appointment_date=appointment_data.get("appointment_date", ""),
            appointment_time=appointment_data.get("appointment_time", ""),
            booking_timestamp=appointment_data.get("booking_timestamp", ""),
            status=appointment_data.get("status", "Confirmed")
        )
    else:
        appointment = appointment_data
    
    return sheets_manager.save_appointment(appointment)

def test_booking() -> str:
    """Test the booking system"""
    from tools.appointment_tools import book_appointment
    print("\n🧪 Testing booking system...")
    result = book_appointment("Test Patient", "Test Problem", "25 September 2025", "10:00 AM")
    print(f"Test result: {result}")
    return result

def test_complete_flow() -> None:
    """Test the complete booking flow with conversation memory"""
    print("\n🧪 Testing complete booking flow...")
    
    # Reset conversation first
    reset_conversation("test_user")
    
    # Test step by step conversation
    print("Step 1: User wants appointment")
    response1 = process_user_message("I want to book an appointment", "test_user")
    print(f"Response 1: {response1}")
    
    print("\nStep 2: User provides name")
    response2 = process_user_message("My name is Test User", "test_user")
    print(f"Response 2: {response2}")
    
    print("\nStep 3: User provides problem")
    response3 = process_user_message("I have fever", "test_user")
    print(f"Response 3: {response3}")
    
    print("\nStep 4: User provides date and time")
    response4 = process_user_message("25 September 2025 at 2:00 PM", "test_user")
    print(f"Response 4: {response4}")

# Export key objects for direct access
appointments_storage = memory_storage.get_appointments_list()  # For backward compatibility
worksheet = sheets_manager.worksheet
sheets_client = sheets_manager.client

# Print initialization status
print("🚀 Hospital appointment system initialized!")
if sheets_manager.is_connected():
    print("✅ Google Sheets integration active")
    print(f"📊 Spreadsheet: {Config.HOSPITAL_NAME} Appointments")
else:
    print("⚠️ Google Sheets integration disabled - using local storage only")
print(f"🏥 {Config.HOSPITAL_NAME} Virtual Receptionist ready to serve!")