"""
Groq API Integration Module for Maahi Robot Assistant
Handles AI-powered responses using Groq's API
"""
from groq import Groq
import logging
from config import GROQ_API_KEY, GROQ_MODEL, GROQ_TEMPERATURE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GroqAssistant:

    def __init__(self, api_key=GROQ_API_KEY):
        if not api_key or api_key == "your_groq_api_key_here":
            raise ValueError(
                "GROQ_API_KEY not set in config.py. "
                "Get your key from https://console.groq.com/keys"
            )
        self.client               = Groq(api_key=api_key)
        self.model                = GROQ_MODEL
        self.temperature          = GROQ_TEMPERATURE
        self.conversation_history = []
        logger.info(f"Groq Assistant initialized with model: {self.model}")

    def get_response(self, user_message):
        try:
            self.conversation_history.append({
                "role":    "user",
                "content": user_message
            })

            logger.info(f"Sending to Groq: {user_message}")

            chat_completion = self.client.chat.completions.create(
                messages    = self.conversation_history,
                model       = self.model,
                temperature = self.temperature,
                max_tokens  = 1024,
            )

            response_text = chat_completion.choices[0].message.content

            self.conversation_history.append({
                "role":    "assistant",
                "content": response_text
            })

            logger.info(f"Groq response: {response_text}")

            # Keep history manageable
            if len(self.conversation_history) > 10:
                self.conversation_history = self.conversation_history[-10:]

            return response_text

        except Exception as e:
            logger.error(f"Error getting response from Groq: {e}")
            return "Sorry, I could not process your request. Please try again."

    def get_simple_response(self, user_message):
        try:
            logger.info(f"Simple query to Groq: {user_message}")

            chat_completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": user_message}],
                model       = self.model,
                temperature = self.temperature,
                max_tokens  = 512,
            )

            response_text = chat_completion.choices[0].message.content
            logger.info(f"Groq response: {response_text}")
            return response_text

        except Exception as e:
            logger.error(f"Error getting simple response: {e}")
            return "I could not understand that. Can you please repeat?"

    def clear_history(self):
        self.conversation_history = []
        logger.info("Conversation history cleared")

    def get_music_recommendation(self, mood_or_genre):
        prompt = (
            f"I want to listen to music. My mood is: {mood_or_genre}. "
            f"Suggest a popular song or artist. Just give me 1-2 songs with artist names."
        )
        return self.get_simple_response(prompt)


if __name__ == "__main__":
    print("Groq Assistant Module Test")
    print("=" * 50)

    try:
        assistant = GroqAssistant()

        print("\n1. Testing simple response...")
        response = assistant.get_simple_response("What is the capital of India?")
        print(f"Question: What is the capital of India?")
        print(f"Answer: {response}\n")

        print("2. Testing music recommendation...")
        recommendation = assistant.get_music_recommendation("happy and energetic")
        print(f"Mood: happy and energetic")
        print(f"Recommendation: {recommendation}\n")

        print("3. Testing conversation context...")
        response1 = assistant.get_response("My name is Alice")
        print(f"Message 1: My name is Alice")
        print(f"Response: {response1}\n")

        response2 = assistant.get_response("What is my name?")
        print(f"Message 2: What is my name?")
        print(f"Response: {response2}\n")

    except Exception as e:
        print(f"Error during testing: {e}")
        print("\nMake sure GROQ_API_KEY is set in config.py")
