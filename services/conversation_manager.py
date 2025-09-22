from typing import Optional, Dict, Any
from langchain.schema import HumanMessage, AIMessage
from storage.memory_storage import memory_storage
from chatbot.chatbot import chatbot, State
from models import ConversationState
import traceback

class ConversationManager:
    """Service for managing user conversations and message processing"""
    
    def __init__(self):
        self.storage = memory_storage
        self.chatbot = chatbot
    
    def process_user_message(self, user_input: str, user_id: str = "default") -> str:
        """Process user message through the graph with session-based context"""
        try:
            print(f"🎯 Processing user input: {user_input} (User: {user_id})")
            
            # Get conversation state for this user
            conversation_state = self.storage.get_or_create_conversation(user_id)
            print(f"📝 User {user_id} conversation has {len(conversation_state['messages'])} messages")
            
            # Convert stored messages to LangChain format and add new user message
            langchain_messages = self._convert_to_langchain_messages(conversation_state['messages'])
            langchain_messages.append(HumanMessage(content=user_input))
            
            # Create state for the graph
            state: State = {"messages": langchain_messages}
            
            # Process the conversation through the chatbot
            final_state = self.chatbot.process_conversation(state)
            assistant_response = self._extract_assistant_response(final_state)
            
            # Update conversation state with both user message and assistant response
            conversation_state["messages"].append(("user", user_input))
            if assistant_response:
                conversation_state["messages"].append(("assistant", assistant_response))
            
            self.storage.update_conversation(user_id, conversation_state)
            
            if assistant_response:
                print(f"✅ Final response: {assistant_response}")
                print(f"📝 User {user_id} conversation updated")
                return assistant_response
            else:
                print("⚠️ No assistant response found")
                return "I apologize, but I couldn't process your request. Please try again."
                
        except Exception as e:
            print(f"❌ Error in process_user_message: {e}")
            traceback.print_exc()
            return f"I apologize, but there was an error: {str(e)}. Please try again."
    
    def _convert_to_langchain_messages(self, stored_messages: list) -> list:
        """Convert stored message tuples to LangChain message objects"""
        langchain_messages = []
        
        for message in stored_messages:
            if isinstance(message, tuple) and len(message) == 2:
                role, content = message
                if role == "user":
                    langchain_messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    langchain_messages.append(AIMessage(content=content))
            elif isinstance(message, (HumanMessage, AIMessage)):
                # Already in correct format
                langchain_messages.append(message)
        
        return langchain_messages
    
    def _extract_assistant_response(self, final_state: Dict[Any, Any]) -> Optional[str]:
        """Extract assistant response from the final state"""
        if not final_state:
            return None
        
        try:
            # Handle different event structures
            if isinstance(final_state, dict):
                # Check if it's a chatbot event
                if 'chatbot' in final_state and 'messages' in final_state['chatbot']:
                    messages = final_state['chatbot']['messages']
                    if isinstance(messages, list) and len(messages) > 0:
                        last_message = messages[-1]
                        if hasattr(last_message, 'content'):
                            return last_message.content
                    elif hasattr(messages, 'content'):
                        return messages.content
                # Check if it has messages directly
                elif 'messages' in final_state:
                    messages = final_state['messages']
                    if isinstance(messages, list) and len(messages) > 0:
                        last_message = messages[-1]
                        if hasattr(last_message, 'content'):
                            return last_message.content
                    elif hasattr(messages, 'content'):
                        return messages.content
            
            return None
            
        except Exception as e:
            print(f"❌ Error extracting assistant response: {e}")
            return None
    
    def reset_conversation(self, user_id: str = "default") -> None:
        """Reset the conversation state for a specific user"""
        self.storage.reset_conversation(user_id)
        print(f"🔄 Conversation reset for user: {user_id}")
    
    def get_conversation_history(self, user_id: str = "default") -> ConversationState:
        """Get conversation history for a user"""
        return self.storage.get_or_create_conversation(user_id)
    
    def get_active_users(self, minutes: int = 30) -> list[str]:
        """Get list of currently active users"""
        return self.storage.get_active_users(minutes)
    
    def cleanup_old_conversations(self, hours: int = 24) -> int:
        """Clean up old inactive conversations"""
        return self.storage.cleanup_old_sessions(hours)
    
    def get_conversation_stats(self) -> Dict[str, Any]:
        """Get conversation statistics"""
        stats = self.storage.get_storage_stats()
        stats.update({
            "active_users_5min": len(self.storage.get_active_users(5)),
            "active_users_15min": len(self.storage.get_active_users(15)),
        })
        return stats

# Global conversation manager instance
conversation_manager = ConversationManager()