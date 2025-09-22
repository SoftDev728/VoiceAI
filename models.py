from typing import Dict, Any, Optional, List
from typing_extensions import TypedDict
from dataclasses import dataclass
from datetime import datetime
import json

@dataclass
class AppointmentData:
    """Data class for appointment information"""
    appointment_id: str
    patient_name: str
    problem: str
    appointment_date: str
    appointment_time: str
    booking_timestamp: str
    status: str = "Confirmed"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert appointment data to dictionary"""
        return {
            "appointment_id": self.appointment_id,
            "patient_name": self.patient_name,
            "problem": self.problem,
            "appointment_date": self.appointment_date,
            "appointment_time": self.appointment_time,
            "booking_timestamp": self.booking_timestamp,
            "status": self.status
        }
    
    def to_row(self) -> List[str]:
        """Convert appointment data to spreadsheet row"""
        return [
            self.appointment_id,
            self.patient_name,
            self.problem,
            self.appointment_date,
            self.appointment_time,
            self.booking_timestamp,
            self.status
        ]
    
    @classmethod
    def create_appointment_id(cls) -> str:
        """Generate unique appointment ID"""
        return f"SH_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    @classmethod
    def create_timestamp(cls) -> str:
        """Generate current timestamp"""
        return datetime.now().strftime('%d %B %Y %H:%M:%S')

@dataclass
class BookingResult:
    """Result of booking operation"""
    success: bool
    message: str
    appointment_details: Optional[AppointmentData] = None
    google_sheets_saved: bool = False
    
    def to_json(self) -> str:
        """Convert result to JSON string"""
        return json.dumps({
            "success": self.success,
            "message": self.message,
            "appointment_details": self.appointment_details.to_dict() if self.appointment_details else None,
            "google_sheets_saved": self.google_sheets_saved
        })

@dataclass
class AppointmentsResponse:
    """Response for appointments retrieval"""
    success: bool
    appointments: List[Dict[str, Any]]
    total_appointments: int
    message: Optional[str] = None
    google_sheets_connected: bool = False
    source: str = "Memory"
    
    def to_json(self) -> str:
        """Convert response to JSON string"""
        return json.dumps({
            "success": self.success,
            "appointments": self.appointments,
            "total_appointments": self.total_appointments,
            "message": self.message,
            "google_sheets_connected": self.google_sheets_connected,
            "source": self.source
        })

class ConversationState(TypedDict):
    """Type definition for conversation state"""
    messages: List[Any]

@dataclass
class ChatMessage:
    """Chat message structure"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

@dataclass
class UserSession:
    """User session data"""
    user_id: str
    conversation_state: ConversationState
    created_at: datetime
    last_active: datetime
    
    def __post_init__(self):
        if not hasattr(self, 'created_at') or not self.created_at:
            self.created_at = datetime.now()
        self.last_active = datetime.now()
    
    def update_activity(self):
        """Update last active timestamp"""
        self.last_active = datetime.now()