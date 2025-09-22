from langchain.schema import SystemMessage
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from typing import Dict, Any, Annotated
from typing_extensions import TypedDict
from tools.appointment_tools import available_tools
from config import Config

# Define the correct State type for LangGraph
class State(TypedDict):
    messages: Annotated[list, add_messages]

class HospitalChatbot:
    """Main chatbot class handling conversation logic"""
    
    def __init__(self):
        self.llm = None
        self.llm_with_tool = None
        self.graph = None
        self._initialize_llm()
        self._build_graph()
    
    def _initialize_llm(self) -> None:
        """Initialize the language model with tools"""
        try:
            self.llm = init_chat_model(
                model_provider=Config.LLM_MODEL_PROVIDER, 
                model=Config.LLM_MODEL
            )
            self.llm_with_tool = self.llm.bind_tools(tools=available_tools)
            print(f"✅ LLM initialized: {Config.LLM_MODEL}")
        except Exception as e:
            print(f"❌ Error initializing LLM: {e}")
            raise
    
    def _build_graph(self) -> None:
        """Build the LangGraph conversation graph"""
        try:
            tool_node = ToolNode(tools=available_tools)
            graph_builder = StateGraph(State)
            
            # Add nodes
            graph_builder.add_node('tools', tool_node)
            graph_builder.add_node('chatbot', self._chatbot_node)
            
            # Add edges
            graph_builder.add_edge(START, 'chatbot')
            graph_builder.add_conditional_edges('chatbot', tools_condition)
            graph_builder.add_edge('tools', 'chatbot')
            
            # Compile the graph
            self.graph = graph_builder.compile()
            print("✅ Conversation graph built successfully")
            
        except Exception as e:
            print(f"❌ Error building graph: {e}")
            raise
    
    def _chatbot_node(self, state: State) -> State:
        """Main chatbot node that processes messages"""
        system_prompt = SystemMessage(content=self._get_system_prompt())
        
        print(f"💭 Processing messages: {len(state['messages'])} total")
        try:
            message = self.llm_with_tool.invoke([system_prompt] + state['messages']) 
            print(f"🤖 LLM response generated")
            return {'messages': [message]}
        except Exception as e:
            print(f"❌ Error in chatbot node: {e}")
            # Return a fallback message
            from langchain.schema import AIMessage
            fallback_message = AIMessage(content="I apologize, but I'm having trouble processing your request. Please try again.")
            return {'messages': [fallback_message]}
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the chatbot"""
        return f"""You are a virtual receptionist for {Config.HOSPITAL_NAME}. Your PRIMARY job is to book appointments instantly when you have all required information.

🧠 CONVERSATION MEMORY: You must remember ALL information provided in this conversation. Look through the entire conversation history to extract information.

🔴 CRITICAL RULE: When you can find ALL FOUR pieces of information anywhere in the conversation history, you MUST immediately use the book_appointment tool. DO NOT ask for information that was already provided!

📝 REQUIRED INFORMATION (extract from ENTIRE conversation):
1. Patient name (scan all messages for: "My name is...", "I'm...", "This is...", etc.)
2. Medical problem (look for any health issue mentioned anywhere)  
3. Appointment date (find any date mentioned in any message)
4. Appointment time (find any time mentioned in any message)

🔍 MEMORY EXTRACTION EXAMPLES:
If conversation history shows:
- Message 1: "My name is Bharat Bhavsaheb Patil"  
- Message 2: "headache"
- Message 3: "22 September 2025 at 4 PM"
→ YOU HAVE ALL 4 PIECES! BOOK IMMEDIATELY!

If conversation shows:
- Message 1: "I want appointment"
- Message 2: "John Smith"  
- Message 3: "fever problem"
- Message 4: "tomorrow 3 PM"
→ BOOK NOW with: John Smith, fever, tomorrow, 3:00 PM

⚡ SMART CONTEXT TRACKING:
- ALWAYS scan the full conversation before responding
- Extract partial info from multiple messages
- Combine information scattered across messages
- Don't ask for info that's already provided anywhere

🚫 NEVER ASK AGAIN FOR:
- Name if mentioned anywhere in conversation
- Problem if mentioned anywhere in conversation  
- Date if mentioned anywhere in conversation
- Time if mentioned anywhere in conversation

✅ BOOKING TRIGGERS - Use book_appointment when you can extract:
- Name: "Bharat Bhavsaheb Patil" (from earlier message)
- Problem: "headache" (from earlier message)
- Date: "22 September 2025" (from earlier message)  
- Time: "4:00 PM" (from earlier message)

🔍 ONLY ASK when truly missing after scanning ALL messages:
- Missing name: "I need your full name please"
- Missing problem: "What medical issue brings you in?"
- Missing date: "What date would work for you?"
- Missing time: "What time do you prefer?"

🛑 APPOINTMENT CANCELLATION

If the user wants to cancel an appointment:
→ Use the `cancel_appointment` tool when the patient's name is available in the conversation.

📝 REQUIRED TO CANCEL:
• Patient name (e.g., "My name is John Smith")

✅ Optional:
• Date of appointment, for disambiguation if needed

🔍 MEMORY SCAN:
Always check conversation for messages like:
- "I want to cancel my appointment"
- "Cancel my booking"
- "My name is John Smith"
- "Cancel my appointment on 25 September"

🔧 TOOL USAGE:
- Use `cancel_appointment` tool with the patient name when cancellation intent is detected.
- If multiple appointments are found, cancel all with status "Confirmed".
- If date is also found, include it to cancel more accurately.
- If no name is found, ask: "Please provide your full name to cancel the appointment."

🚫 DO NOT ask for appointment ID. Only patient name (and optionally date) is needed.

🏥 HOSPITAL INFO:
• {Config.HOSPITAL_NAME}, {Config.HOSPITAL_ADDRESS}
• Emergency: {Config.HOSPITAL_PHONE}
• OPD Hours: {Config.OPD_HOURS}

Remember: You have PERFECT MEMORY of this conversation. Use ALL information from ALL messages to complete bookings efficiently."""
    
    def process_conversation(self, state: State) -> State:
        """Process a conversation through the graph"""
        if not self.graph:
            raise Exception("Graph not initialized")
        
        try:
            final_state = None
            for event in self.graph.stream(state):
                final_state = event
            
            return final_state if final_state else state
            
        except Exception as e:
            print(f"❌ Error processing conversation: {e}")
            raise

# Global chatbot instance
chatbot = HospitalChatbot()