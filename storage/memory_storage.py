from typing import List, Dict, Any
from models import AppointmentData, AppointmentsResponse, UserSession, ConversationState
from datetime import datetime
import uuid

class MemoryStorage:
    """In-memory storage manager for appointments and user sessions"""
    
    def __init__(self):
        self.appointments: List[AppointmentData] = []
        self.user_conversations: Dict[str, ConversationState] = {}
        self.user_sessions: Dict[str, UserSession] = {}
    
    # Appointment Storage Methods
    def save_appointment(self, appointment_data: AppointmentData) -> bool:
        """Save appointment to memory storage"""
        try:
            self.appointments.append(appointment_data)
            print(f"✅ Appointment {appointment_data.appointment_id} stored in memory")
            return True
        except Exception as e:
            print(f"❌ Failed to save appointment to memory: {e}")
            return False
    
    def get_all_appointments(self) -> AppointmentsResponse:
        """Retrieve all appointments from memory"""
        try:
            appointments_dict = [appointment.to_dict() for appointment in self.appointments]
            return AppointmentsResponse(
                success=True,
                appointments=appointments_dict,
                total_appointments=len(appointments_dict),
                source="Memory",
                google_sheets_connected=False
            )
        except Exception as e:
            return AppointmentsResponse(
                success=False,
                message=f"Error retrieving appointments from memory: {str(e)}",
                appointments=[],
                total_appointments=0,
                source="Memory"
            )
    
    def get_appointments_list(self) -> List[AppointmentData]:
        """Get raw appointments list for backward compatibility"""
        return self.appointments
    
    def clear_appointments(self) -> None:
        """Clear all appointments from memory"""
        self.appointments.clear()
        print("🗑️ All appointments cleared from memory")
    
    # Conversation Management Methods
    def get_or_create_conversation(self, user_id: str) -> ConversationState:
        """Get or create conversation state for a specific user"""
        if user_id not in self.user_conversations:
            self.user_conversations[user_id] = {"messages": []}
            print(f"🆕 Created new conversation for user: {user_id}")
        
        # Update user session activity
        self._update_user_session(user_id)
        return self.user_conversations[user_id]
    
    def reset_conversation(self, user_id: str) -> None:
        """Reset the conversation state for a specific user"""
        if user_id in self.user_conversations:
            del self.user_conversations[user_id]
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]
        print(f"🔄 Conversation reset for user: {user_id}")
    
    def update_conversation(self, user_id: str, conversation_state: ConversationState) -> None:
        """Update conversation state for a user"""
        self.user_conversations[user_id] = conversation_state
        self._update_user_session(user_id)
    
    def get_conversation_count(self) -> int:
        """Get total number of active conversations"""
        return len(self.user_conversations)
    
    # User Session Management
    def _update_user_session(self, user_id: str) -> None:
        """Update or create user session"""
        if user_id in self.user_sessions:
            self.user_sessions[user_id].update_activity()
        else:
            self.user_sessions[user_id] = UserSession(
                user_id=user_id,
                conversation_state=self.user_conversations.get(user_id, {"messages": []}),
                created_at=datetime.now(),
                last_active=datetime.now()
            )
    
    def get_user_session(self, user_id: str) -> UserSession:
        """Get user session information"""
        return self.user_sessions.get(user_id)
    
    def get_active_users(self, minutes: int = 30) -> List[str]:
        """Get list of users active within specified minutes"""
        cutoff_time = datetime.now().timestamp() - (minutes * 60)
        active_users = []
        
        for user_id, session in self.user_sessions.items():
            if session.last_active.timestamp() > cutoff_time:
                active_users.append(user_id)
        
        return active_users
    
    def cleanup_old_sessions(self, hours: int = 24) -> int:
        """Clean up old inactive sessions"""
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        users_to_remove = []
        
        for user_id, session in self.user_sessions.items():
            if session.last_active.timestamp() < cutoff_time:
                users_to_remove.append(user_id)
        
        for user_id in users_to_remove:
            self.reset_conversation(user_id)
        
        print(f"🧹 Cleaned up {len(users_to_remove)} old sessions")
        return len(users_to_remove)
    
    # Utility Methods
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        return {
            "total_appointments": len(self.appointments),
            "active_conversations": len(self.user_conversations),
            "total_users": len(self.user_sessions),
            "active_users_30min": len(self.get_active_users(30)),
            "memory_usage": {
                "appointments_count": len(self.appointments),
                "conversations_count": len(self.user_conversations),
                "sessions_count": len(self.user_sessions)
            }
        }

# Global instance
memory_storage = MemoryStorage()