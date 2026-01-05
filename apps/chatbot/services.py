import logging
import os
from django.conf import settings

logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("Optional dependency 'openai' not found.")

try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("Optional dependency 'google-genai' not found.")

class AIService:
    def __init__(self):
        self.openai_key = getattr(settings, "OPENAI_API_KEY", None)
        self.gemini_key = getattr(settings, "GEMINI_API_KEY", None)
        
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
                    
                    if self.available_gemini_models:
                        logger.info(f"Detected Gemini models: {self.available_gemini_models}")
                except Exception as list_err:
                    logger.warning(f"Failed to list Gemini models: {str(list_err)}")
            except Exception as e:
                logger.error(f"Error initializing Gemini client: {str(e)}")

    def get_system_prompt(self):
        return (
            "You are the Welleazy AI Health Assistant. Your goal is to help users with their health-related "
            "queries and guide them to Welleazy's services. Welleazy provides: "
            "1. Doctor Consultations (In-person, Video, Tele-consultation) "
            "2. Diagnostic/Lab Tests (including home collection) "
            "3. Health Records management "
            "4. Insurance Records management "
            "5. Pharmacy services "
            "6. Health Assessments "
            "7. Care Programs "
            "Be professional, empathetic, and always advise users to consult a doctor for a definitive diagnosis."
        )

    def get_chat_response(self, messages_history):
        if self.gemini_client and GEMINI_AVAILABLE:
            return self._get_gemini_response(messages_history)
        
        if self.openai_client:
            return self._get_openai_response(messages_history)
        
        return "AI service unavailable. Please check your API keys."

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
        for pm in priority_models:
            if pm in self.available_gemini_models or pm.replace('models/', '') in [m.replace('models/', '') for m in self.available_gemini_models]:
                models_to_try.append(pm)
        
        for am in self.available_gemini_models:
            if am not in models_to_try:
                models_to_try.append(am)
                
        if not models_to_try:
            models_to_try = ['gemini-1.5-flash', 'gemini-pro']

        last_error = ""
        for model_name in models_to_try:
            try:
                contents = []
                for msg in messages_history:
                    role = 'user' if msg['role'] == 'user' else 'model'
                    contents.append({
                        'role': role,
                        'parts': [{'text': msg['content']}]
                    })

                response = self.gemini_client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config={
                        'system_instruction': self.get_system_prompt(),
                    }
                )
                if response and response.text:
                    return response.text
                return "Gemini returned an empty response."
            except Exception as e:
                last_error = str(e)
                if "404" not in last_error and "not found" not in last_error.lower():
                    logger.error(f"Gemini error with {model_name}: {last_error}")
                else:
                    logger.warning(f"Gemini model {model_name} failed: {last_error}")

        return f"Gemini Error: All attempted models failed. Available for your key: {self.available_gemini_models}. Last error: {last_error}"

    def _get_openai_response(self, messages_history):
        try:
            messages = [{"role": "system", "content": self.get_system_prompt()}]
            messages.extend(messages_history)
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API Error: {str(e)}")
            return f"OpenAI Error: {str(e)}"
