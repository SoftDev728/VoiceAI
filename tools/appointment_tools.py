from langchain_core.tools import tool
from typing import Dict, Any
from models import AppointmentData, BookingResult
from storage.memory_storage import memory_storage
from storage.sheets_manager import sheets_manager
from config import Config
import json
import re
from datetime import datetime

def normalize_date(text_date: str) -> str:
    """Convert '22nd September 2025' -> '22 September 2025'"""
    return re.sub(r'(st|nd|rd|th)', '', text_date).strip().lower()

@tool
def book_appointment(patient_name: str, problem: str, appointment_date: str, appointment_time: str) -> str:
    """
    Book a new appointment for a patient at Surat Hospital.
    
    Args:
        patient_name: Full name of the patient
        problem: Medical problem or reason for visit
        appointment_date: Date of appointment (format: 22 September 2025)
        appointment_time: Time of appointment (format: 4:00 PM)
    
    Returns:
        JSON string with booking confirmation and appointment details
    """
    print("🏥 Processing appointment booking...")
    try:
        print(f"   Patient: {patient_name}")
        print(f"   Problem: {problem}")
        print(f"   Date: {appointment_date}")
        print(f"   Time: {appointment_time}")
        
        # Create appointment data
        appointment_data = AppointmentData(
            appointment_id=AppointmentData.create_appointment_id(),
            patient_name=patient_name,
            problem=problem,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            booking_timestamp=AppointmentData.create_timestamp()
        )
        
        # Save to memory storage (always works)
        memory_saved = memory_storage.save_appointment(appointment_data)
        if not memory_saved:
            raise Exception("Failed to save appointment to memory storage")
        
        # Try to save to Google Sheets
        sheets_saved = sheets_manager.save_appointment(appointment_data)
        
        # Prepare success message
        storage_info = "and saved to Google Sheets" if sheets_saved else "(saved locally)"
        
        success_message = _create_booking_confirmation_message(appointment_data, storage_info)
        
        result = BookingResult(
            success=True,
            message=success_message,
            appointment_details=appointment_data,
            google_sheets_saved=sheets_saved
        )
        
        print(f"✅ Booking completed successfully!")
        return result.to_json()
        
    except Exception as e:
        error_msg = f"❌ Sorry, there was an error booking your appointment: {str(e)}. Please try again or contact our staff at {Config.HOSPITAL_PHONE}."
        print(f"❌ Error booking appointment: {e}")
        
        error_result = BookingResult(
            success=False,
            message=error_msg,
            google_sheets_saved=False
        )
        return error_result.to_json()

@tool
def get_all_appointments() -> str:
    """
    Retrieve all appointments stored in the hospital system.
    
    Returns:
        JSON string containing array of all appointment objects with total count
    """
    try:
        response = memory_storage.get_all_appointments()
        response.google_sheets_connected = sheets_manager.is_connected()
        return response.to_json()
        
    except Exception as e:
        error_response = memory_storage.get_all_appointments()
        error_response.success = False
        error_response.message = f"Error retrieving appointments: {str(e)}"
        return error_response.to_json()

@tool 
def get_appointments_from_sheets() -> str:
    """
    Retrieve all appointments directly from Google Sheets.
    
    Returns:
        JSON string with appointments from Google Sheets
    """
    try:
        response = sheets_manager.get_all_appointments()
        return response.to_json()
    except Exception as e:
        error_response = sheets_manager.get_all_appointments()
        error_response.success = False
        error_response.message = f"Unexpected error reading from Google Sheets: {str(e)}"
        return error_response.to_json()

def _create_booking_confirmation_message(appointment_data: AppointmentData, storage_info: str) -> str:
    """Create a formatted booking confirmation message"""
    return f"""🎉 Appointment booked successfully {storage_info}!

📋 **Appointment Details:**
• **Appointment ID:** {appointment_data.appointment_id}
• **Patient Name:** {appointment_data.patient_name}
• **Medical Issue:** {appointment_data.problem}
• **Date:** {appointment_data.appointment_date}
• **Time:** {appointment_data.appointment_time}
• **Status:** {appointment_data.status}

📝 **Important Instructions:**
• Please arrive 15 minutes early
• Bring a valid ID proof
• Bring any previous medical records if available
• Contact us at {Config.HOSPITAL_PHONE} for any changes

🏥 **{Config.HOSPITAL_NAME}**
📍 {Config.HOSPITAL_ADDRESS}"""

@tool
def cancel_appointment(patient_name: str, appointment_date: str = "") -> str:
    """
    Cancel appointment based on patient name (and optionally date).
    """
    try:
        normalized_name = patient_name.strip().lower()
        normalized_date = normalize_date(appointment_date) if appointment_date else ""

        # Fetch appointments
        appointments = memory_storage.get_all_appointments().appointments

        matching = [
            appt for appt in appointments
            if appt.patient_name.strip().lower() == normalized_name
            and (normalize_date(appt.appointment_date) == normalized_date if normalized_date else True)
            and appt.status.strip().lower() != "cancelled"
        ]

        if not matching:
            return json.dumps({
                "success": False,
                "message": f"No active appointments found for '{patient_name}'{' on ' + appointment_date if appointment_date else ''}."
            })

        for appt in matching:
            appt.status = "Cancelled"

        cancelled_ids = [appt.appointment_id for appt in matching]
        sheet_updated = sheets_manager.cancel_appointments_by_ids(cancelled_ids)

        return json.dumps({
            "success": True,
            "message": f"✅ Cancelled {len(matching)} appointment(s) for '{patient_name}'",
            "cancelled_ids": cancelled_ids,
            "google_sheets_updated": sheet_updated
        })

    except Exception as e:
        return json.dumps({
            "success": False,
            "message": f"Error cancelling appointment: {str(e)}"
        })
# List of available tools for export
available_tools = [book_appointment, get_all_appointments, get_appointments_from_sheets,cancel_appointment]