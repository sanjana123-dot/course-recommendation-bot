import os
import json
import logging
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types
import streamlit as st
# from dotenv import load_dotenv

# # Load environment variables from .env file
# load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CourseChatbot:
    def __init__(self, rag_system):
        """
        Initialize the chatbot with RAG system and Gemini API
        
        Args:
            rag_system: Instance of CourseRAGSystem
        """
        self.rag_system = rag_system
               
        # Try to get API key from Streamlit secrets first, then environment variables
        try:
            self.api_key = st.secrets["GEMINI_API_KEY"]
        except:
            self.api_key = os.getenv("GEMINI_API_KEY", "")
        
        if not self.api_key:
            logger.error("GEMINI_API_KEY not found in environment variables")
            raise ValueError("GEMINI_API_KEY is required. Please add it to Streamlit Cloud secrets or your .env file")
        
        try:
            self.client = genai.Client(api_key=self.api_key)
            logger.info("Gemini client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            raise
    
    def format_course_info(self, course: Dict[str, Any]) -> str:
        """
        Format course information for display
        
        Args:
            course: Course dictionary
            
        Returns:
            Formatted course information string
        """
        return f"""
**{course['title']}**
- **Category:** {course['category']}
- **Difficulty:** {course['difficulty']}
- **Duration:** {course['duration']}
- **Skills:** {', '.join(course['skills'])}
- **Prerequisites:** {course['prerequisites']}
- **Provider:** {course['provider']}
- **Rating:** {course['rating']}/5.0 ({course['enrollment_count']} students)
- **Description:** {course['description']}
"""
    
    def create_context_from_courses(self, courses: List[Dict[str, Any]]) -> str:
        """
        Create context string from course recommendations
        
        Args:
            courses: List of course dictionaries
            
        Returns:
            Context string for the LLM
        """
        if not courses:
            return "No relevant courses found in the database."
        
        context = "Here are the relevant courses from our database:\n\n"
        for i, course in enumerate(courses, 1):
            context += f"{i}. {course['title']}\n"
            context += f"   Category: {course['category']}\n"
            context += f"   Difficulty: {course['difficulty']}\n"
            context += f"   Duration: {course['duration']}\n"
            context += f"   Skills: {', '.join(course['skills'])}\n"
            context += f"   Prerequisites: {course['prerequisites']}\n"
            context += f"   Description: {course['description']}\n"
            context += f"   Provider: {course['provider']}\n"
            context += f"   Rating: {course['rating']}/5.0\n\n"
        
        return context
    
    def generate_response(self, 
                         user_message: str, 
                         user_interests: str = "", 
                         user_background: str = "", 
                         skill_level: str = "") -> str:
        """
        Generate a response using RAG and Gemini API
        
        Args:
            user_message: User's message
            user_interests: User's interests
            user_background: User's background
            skill_level: User's skill level
            
        Returns:
            Generated response
        """
        try:
            # Get course recommendations using RAG
            recommendations = self.rag_system.get_recommendations(
                user_interests=user_interests or user_message,
                user_background=user_background,
                skill_level=skill_level,
                top_k=5
            )
            
            # Create context from recommendations
            context = self.create_context_from_courses(recommendations)
            
            # Create system prompt
            system_prompt = """
You are a helpful course recommendation assistant. Your role is to help users find the most suitable learning paths and courses based on their interests, background, and skill level.

Guidelines:
1. Use the provided course database to make recommendations
2. Be personalized and consider the user's specific needs
3. Explain why certain courses are recommended
4. Suggest learning paths when appropriate
5. Be encouraging and supportive
6. If no perfect match exists, suggest the closest alternatives
7. Always reference specific courses from the database
8. Provide practical advice on how to get started

Always base your recommendations on the course database provided in the context.
"""
            
            # Create user prompt with context
            user_prompt = f"""
User Context:
- Interests: {user_interests}
- Background: {user_background}
- Skill Level: {skill_level}
- Message: {user_message}

Course Database Context:
{context}

Please provide personalized course recommendations based on the user's needs and the available courses in the database.
"""
            
            # Generate response using Gemini
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    types.Content(role="user", parts=[types.Part(text=user_prompt)])
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.7,
                    max_output_tokens=1000
                )
            )
            
            if response.text:
                return response.text
            else:
                return "I apologize, but I'm having trouble generating a response right now. Please try again."
        
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"I encountered an error while processing your request: {str(e)}. Please try again or contact support if the issue persists."
    
    def extract_user_info(self, conversation_history: List[Dict[str, str]]) -> Dict[str, str]:
        """
        Extract user information from conversation history
        
        Args:
            conversation_history: List of conversation messages
            
        Returns:
            Dictionary with extracted user information
        """
        user_info = {
            "interests": "",
            "background": "",
            "skill_level": ""
        }
        
        # Simple extraction from conversation history
        for message in conversation_history:
            if message["role"] == "user":
                text = message["content"].lower()
                
                # Extract interests
                if any(keyword in text for keyword in ["interested in", "want to learn", "goal", "passion"]):
                    user_info["interests"] += " " + message["content"]
                
                # Extract background
                if any(keyword in text for keyword in ["experience", "background", "worked as", "studied"]):
                    user_info["background"] += " " + message["content"]
                
                # Extract skill level
                if any(keyword in text for keyword in ["beginner", "intermediate", "advanced", "new to", "expert"]):
                    if "beginner" in text or "new to" in text:
                        user_info["skill_level"] = "Beginner"
                    elif "intermediate" in text:
                        user_info["skill_level"] = "Intermediate"
                    elif "advanced" in text or "expert" in text:
                        user_info["skill_level"] = "Advanced"
        
        return user_info
