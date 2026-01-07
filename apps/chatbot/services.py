import logging
import os
from django.conf import settings
from django.db.models import Q
from datetime import datetime

# Import modular tools
from .tools import ChatbotTools

logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("Optional dependency 'openai' not found.")

try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("Optional dependency 'google-genai' not found.")

class AIService:
    def __init__(self, user=None):
        self.user = user
        self.openai_key = getattr(settings, "OPENAI_API_KEY", None)
        self.gemini_key = getattr(settings, "GEMINI_API_KEY", None)
        
        self.tools = ChatbotTools(user)
        
        self.openai_client = None
        if OPENAI_AVAILABLE and self.openai_key:
            self.openai_client = OpenAI(api_key=self.openai_key)
        
        self.gemini_client = None
        self.available_gemini_models = []
        if GEMINI_AVAILABLE and self.gemini_key:
            try:
                self.gemini_client = genai.Client(api_key=self.gemini_key)
                try:
                    for m in self.gemini_client.models.list():
                        self.available_gemini_models.append(m.name)
                except Exception as list_err:
                    logger.warning(f"Failed to list Gemini models: {str(list_err)}")
            except Exception as e:
                logger.error(f"Error initializing Gemini client: {str(e)}")

    def _get_tools_list(self):
        # List of tools exposed to the chatbot service
        return [
            self.tools.get_user_profile,
            self.tools.get_user_appointments,
            self.tools.get_user_health_vitals,
            self.tools.get_user_medical_documents,
            self.tools.get_user_medicine_reminders,
            self.tools.get_user_medical_history,
            self.tools.get_user_medical_bills,
            self.tools.get_user_insurance_policies,
            self.tools.search_lab_services,
            self.tools.search_medicines,
            self.tools.get_pharmacy_cart,
            self.tools.get_pharmacy_order_history,
            self.tools.get_user_care_program_bookings,
            self.tools.get_user_health_assessment,
            self.tools.search_doctors,
            self.tools.get_user_gym_vouchers,
            self.tools.search_gym_packages,
            self.tools.get_user_eye_dental_bookings,
            self.tools.get_woman_cycle_prediction,
            self.tools.get_user_notifications,
            self.tools.get_available_care_programs,
            self.tools.get_doctor_specialties,
        ]

    # Core chatbot logic

    def get_system_prompt(self):
        return (
            "Help users with their health queries and guide them to Welleazy's services like "
            "doctor consultations, lab tests, medical records, insurance, pharmacy, and wellness.\n\n"
            "Available tools:\n"
            "- User info: get_user_profile, get_user_medical_history, get_user_medical_documents\n"
            "- Vitals/Meds: get_user_health_vitals, get_user_medicine_reminders\n"
            "- Appointments: get_user_appointments, get_user_medical_bills, get_user_insurance_policies\n"
            "- Search: search_lab_services, search_medicines, search_doctors, search_gym_packages\n"
            "- Cart/Orders: get_pharmacy_cart, get_pharmacy_order_history\n"
            "- Wellness & Assessments**: `get_user_care_program_bookings`, `get_user_health_assessment`, `get_user_gym_vouchers`, `get_user_eye_dental_bookings`, `get_woman_cycle_prediction`.\n"
            "- Discovery: `get_available_care_programs`, `get_doctor_specialties`.\n"
            "- Alerts: `get_user_notifications`.\n\n"
            "Notes:\n"
            "1. If a user asks what 'types' of services exist (like care programs or specialties), use the discovery tools.\n"
            "2. Search tools for lab tests and meds handle typos/broad queries. If asked generally, search by category name.\n"
            "2. Always mention the patient_name or patient when showing records.\n"
            "3. Stay professional and empathetic, but always advise consulting a doctor for real diagnosis."
        )

    def get_chat_response(self, messages_history):
        response = None
        if self.gemini_client and GEMINI_AVAILABLE:
            response = self._get_gemini_response(messages_history)
            
            # If it's a quota error or other failure, we still try OpenAI if requested/available
            if response == "__GEMINI_QUOTA_EXCEEDED__" or response == "__GEMINI_ERROR__":
                logger.info("Gemini failed or quota exceeded, attempting fallback to OpenAI...")
            elif not response.startswith("__"):
                return response
        
        if self.openai_client and self.openai_key and self.openai_key != "None":
            return self._get_openai_response(messages_history)
        
        # Final fallback error messages
        if response == "__GEMINI_QUOTA_EXCEEDED__":
            return "Gemini Quota Exceeded. Please try again in a few minutes."
        
        return "Unable to connect to the assistant service right now. Please try again later."

    def _get_gemini_response(self, messages_history):
        priority_models = [
            'gemini-1.5-flash', 
            'gemini-1.5-flash-latest', 
            'gemini-1.5-pro', 
            'gemini-pro',
            'models/gemini-1.5-flash',
            'models/gemini-1.5-pro',
            'models/gemini-pro'
        ]
        
        models_to_try = []
        for am in self.available_gemini_models:
            if am not in models_to_try:
                models_to_try.append(am)
        
        for pm in priority_models:
            if pm not in models_to_try:
                models_to_try.append(pm)
        
        last_error = ""
        for model_name in models_to_try:
            try:
                contents = []
                for msg in messages_history:
                    role = 'user' if msg['role'] == 'user' else 'model'
                    contents.append({'role': role, 'parts': [{'text': msg['content']}]})

                # Define tools for Gemini
                search_query_tools = ['search_lab_services', 'search_medicines', 'search_gym_packages']
                tool_declarations = []
                for t in self._get_tools_list():
                    # Default: no parameters
                    params = types.Schema(type='OBJECT', properties={})
                    
                    if t.__name__ in search_query_tools:
                        params = types.Schema(
                            type='OBJECT',
                            properties={'query': types.Schema(type='STRING', description='Search query (can be specific name or broad category)')},
                            required=['query']
                        )
                    elif t.__name__ == 'search_doctors':
                        params = types.Schema(
                            type='OBJECT',
                            properties={
                                'query': types.Schema(type='STRING', description='Doctor name or specialty'),
                                'city': types.Schema(type='STRING', description='City name')
                            }
                        )

                    tool_declarations.append(types.FunctionDeclaration(
                        name=t.__name__,
                        description=t.__doc__,
                        parameters=params
                    ))

                tools = [types.Tool(function_declarations=tool_declarations)]

                response = self.gemini_client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config={
                        'system_instruction': self.get_system_prompt(),
                        'tools': tools
                    }
                )

                # Handle tool execution
                if response.candidates and response.candidates[0].content.parts:
                    has_tool_call = False
                    for part in response.candidates[0].content.parts:
                        if part.function_call:
                            has_tool_call = True
                            func_name = part.function_call.name
                            args = part.function_call.args
                            
                            logger.info(f"AI requested tool: {func_name} with args {args}")
                            
                            tool_func = getattr(self.tools, func_name)
                            result = tool_func(**args) if args else tool_func()
                            
                            contents.append(response.candidates[0].content)
                            contents.append(types.Content(
                                role='tool',
                                parts=[types.Part.from_function_response(
                                    name=func_name,
                                    response={'result': result}
                                )]
                            ))
                            
                            # Final generation after tool call
                            final_response = self.gemini_client.models.generate_content(
                                model=model_name,
                                contents=contents,
                                config={
                                    'system_instruction': self.get_system_prompt(),
                                    'tools': tools
                                }
                            )
                            return final_response.text
                    
                    if not has_tool_call:
                        return response.text
                
                return response.text

            except Exception as e:
                last_error = str(e)
                if "404" in last_error or "not found" in last_error.lower():
                    logger.warning(f"Gemini model {model_name} failed with 404, trying next...")
                    continue
                elif "429" in last_error or "quota" in last_error.lower():
                    logger.warning(f"Gemini Quota Exceeded.")
                    return "__GEMINI_QUOTA_EXCEEDED__"
                else:
                    logger.error(f"Gemini error: {last_error}")
                    return "__GEMINI_ERROR__"

        return f"Gemini Error: All attempted models failed. Last error: {last_error}"

    def _get_openai_response(self, messages_history):
        try:
            messages = [{"role": "system", "content": self.get_system_prompt()}]
            messages.extend(messages_history)
            
            search_query_tools = ['search_lab_services', 'search_medicines', 'search_gym_packages']
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": t.__name__,
                        "description": t.__doc__,
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "Search term (specific or broad)"},
                                "city": {"type": "string", "description": "City name"}
                            } if t.__name__ == 'search_doctors' else (
                                {
                                    "type": "object",
                                    "properties": {
                                        "query": {"type": "string", "description": "Search term (specific or broad)"}
                                    },
                                    "required": ["query"]
                                } if t.__name__ in search_query_tools else {"type": "object", "properties": {}}
                            ),
                            "required": ["query"] if t.__name__ in search_query_tools else []
                        }
                    }
                } for t in self._get_tools_list()
            ]

            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=tools,
                tool_choice="auto"
            )
            
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            if tool_calls:
                messages.append(response_message)
                for tool_call in tool_calls:
                    func_name = tool_call.function.name
                    import json
                    args = json.loads(tool_call.function.arguments)
                    
                    tool_func = getattr(self.tools, func_name)
                    result = tool_func(**args) if args else tool_func()
                    
                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": func_name,
                        "content": str(result),
                    })
                
                final_response = self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                )
                return final_response.choices[0].message.content

            return response_message.content
        except Exception as e:
            logger.error(f"OpenAI API Error: {str(e)}")
            return f"OpenAI Error: {str(e)}"
