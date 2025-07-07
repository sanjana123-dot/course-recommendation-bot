import streamlit as st
import json
import logging
from typing import List, Dict, Any

# Import custom modules
from simple_rag_system import SimpleCourseRAGSystem
from chatbot import CourseChatbot

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Course Recommendation Bot",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        margin-bottom: 30px;
        font-size: 3em;
        font-weight: bold;
    }
    .chat-message {
        padding: 15px;
        border-radius: 15px;
        margin: 15px 0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 5px solid #2196f3;
        margin-left: 20px;
    }
    .bot-message {
        background-color: #f3e5f5;
        border-left: 5px solid #9c27b0;
        margin-right: 20px;
    }
    .course-card {
        border: 2px solid #e0e0e0;
        border-radius: 12px;
        padding: 20px;
        margin: 15px 0;
        background: linear-gradient(135deg, #fafafa 0%, #f5f5f5 100%);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: transform 0.2s;
    }
    .course-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    .sidebar-section {
        margin-bottom: 25px;
        padding: 15px;
        background-color: #f8f9fa;
        border-radius: 10px;
        border: 1px solid #e9ecef;
    }

    .featured-course {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        border: 2px solid #ff9800;
    }
    .search-results {
        background-color: #e8f5e8;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #4caf50;
        margin: 10px 0;
    }
    .profile-section {
        background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .chat-container {
        max-height: 500px;
        overflow-y: auto;
        padding: 10px;
        background-color: #fafafa;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
    }
    .input-container {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        border: 2px solid #e0e0e0;
        margin-top: 10px;
    }
    .category-chip {
        display: inline-block;
        background-color: #e3f2fd;
        color: #1976d2;
        padding: 5px 10px;
        border-radius: 20px;
        margin: 2px;
        font-size: 0.9em;
        border: 1px solid #bbdefb;
    }
    .difficulty-badge {
        padding: 5px 10px;
        border-radius: 15px;
        font-size: 0.8em;
        font-weight: bold;
        margin: 2px;
    }
    .beginner { background-color: #c8e6c9; color: #2e7d32; }
    .intermediate { background-color: #fff3e0; color: #ef6c00; }
    .advanced { background-color: #ffcdd2; color: #c62828; }
    .rating-stars {
        color: #ffc107;
        font-size: 1.2em;
    }
    .enrollment-count {
        color: #666;
        font-size: 0.9em;
        font-style: italic;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'user_profile' not in st.session_state:
    st.session_state.user_profile = {
        "interests": "",
        "background": "",
        "skill_level": ""
    }
if 'rag_system' not in st.session_state:
    st.session_state.rag_system = None
if 'chatbot' not in st.session_state:
    st.session_state.chatbot = None
if 'show_welcome' not in st.session_state:
    st.session_state.show_welcome = True
if 'search_history' not in st.session_state:
    st.session_state.search_history = []

@st.cache_resource
def initialize_rag_system():
    """Initialize and cache the RAG system"""
    try:
        with st.spinner("Loading course database..."):
            return SimpleCourseRAGSystem()
    except Exception as e:
        st.error(f"Failed to initialize RAG system: {e}")
        return None

@st.cache_resource
def initialize_chatbot(_rag_system):
    """Initialize and cache the chatbot"""
    try:
        with st.spinner("Initializing AI assistant..."):
            return CourseChatbot(_rag_system)
    except Exception as e:
        st.error(f"Failed to initialize chatbot: {e}")
        return None

def display_course_card(course: Dict[str, Any]) -> None:
    """Display a course in a card format"""
    difficulty_class = course['difficulty'].lower()
    
    with st.container():
        st.markdown(f"""
        <div class="course-card">
            <h3 style="color: #1f77b4; margin-bottom: 15px;">{course['title']}</h3>
            <div style="margin-bottom: 10px;">
                <span class="category-chip">{course['category']}</span>
                <span class="difficulty-badge {difficulty_class}">{course['difficulty']}</span>
            </div>
            <div style="margin-bottom: 10px;">
                <strong>Duration:</strong> {course['duration']} | 
                <strong>Provider:</strong> {course['provider']}
            </div>
            <div style="margin-bottom: 10px;">
                <strong>Skills:</strong> {', '.join(course['skills'])}
            </div>
            <div style="margin-bottom: 10px;">
                <strong>Prerequisites:</strong> {course['prerequisites']}
            </div>
            <div style="margin-bottom: 15px;">
                <span class="rating-stars">{'⭐' * int(course['rating'])}</span> 
                <strong>{course['rating']}/5.0</strong>
                <span class="enrollment-count">({course['enrollment_count']} students enrolled)</span>
            </div>
            <div style="background-color: #f8f9fa; padding: 10px; border-radius: 5px; border-left: 3px solid #007bff;">
                <strong>Description:</strong> {course['description']}
            </div>
        </div>
        """, unsafe_allow_html=True)

def display_welcome_message():
    """Display welcome message and instructions"""
    if st.session_state.show_welcome:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; padding: 25px; border-radius: 15px; margin: 20px 0;">
            <h2 style="margin-bottom: 15px;">🎉 Welcome to Your Personal Course Advisor!</h2>
            <p style="font-size: 1.1em; margin-bottom: 15px;">
                I'm here to help you discover the perfect learning path based on your interests, 
                background, and goals. Here's how to get started:
            </p>
            <ol style="font-size: 1.0em; margin-left: 20px;">
                <li><strong>Set up your profile</strong> in the sidebar (interests, background, skill level)</li>
                <li><strong>Chat with me</strong> about what you want to learn</li>
                <li><strong>Get personalized recommendations</strong> from our course database</li>
                <li><strong>Explore courses</strong> with detailed information and ratings</li>
            </ol>
            <p style="margin-top: 15px; font-style: italic;">
                💡 Try asking: "I want to learn web development as a beginner" or 
                "Recommend data science courses for someone with programming experience"
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Got it! Let's start", key="welcome_dismiss"):
            st.session_state.show_welcome = False
            st.rerun()



def display_search_suggestions():
    """Display search suggestions for users"""
    suggestions = [
        "Python programming for beginners",
        "Advanced machine learning",
        "Web development with JavaScript",
        "Data science projects",
        "Cloud computing with AWS",
        "Mobile app development",
        "Cybersecurity fundamentals",
        "UI/UX design principles"
    ]
    
    st.markdown("**🔍 Quick Search Suggestions:**")
    cols = st.columns(2)
    for i, suggestion in enumerate(suggestions[:6]):
        with cols[i % 2]:
            if st.button(suggestion, key=f"suggest_{i}"):
                # Perform search when suggestion is clicked
                results = st.session_state.rag_system.search_courses(suggestion, top_k=3)
                if results:
                    st.markdown('<div class="search-results">', unsafe_allow_html=True)
                    st.markdown(f"#### 🎯 Results for '{suggestion}':")
                    for course in results:
                        with st.expander(f"📚 {course['title']} ({course['similarity_score']:.2f})"):
                            display_course_card(course)
                    st.markdown('</div>', unsafe_allow_html=True)

def main():
    """Main application function"""
    
    # Header
    st.markdown("""
    <div class="main-header">
        🎓 Course Recommendation Bot
    </div>
    <div style="text-align: center; color: #666; margin-bottom: 30px;">
        <p style="font-size: 1.3em;">Your AI-powered learning companion for personalized course recommendations</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Initialize systems
    if st.session_state.rag_system is None:
        st.session_state.rag_system = initialize_rag_system()
    
    if st.session_state.rag_system is None:
        st.error("❌ Failed to initialize the course recommendation system. Please check your configuration.")
        st.stop()
    
    if st.session_state.chatbot is None:
        st.session_state.chatbot = initialize_chatbot(st.session_state.rag_system)
    
    if st.session_state.chatbot is None:
        st.error("❌ Failed to initialize the AI chatbot. Please check your GEMINI_API_KEY in the .env file.")
        st.stop()
    
    # Display welcome message
    display_welcome_message()
    
    # Sidebar for user profile and search
    with st.sidebar:
        st.markdown('<div class="profile-section">', unsafe_allow_html=True)
        st.markdown("### 👤 Your Learning Profile")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # User interests
        st.markdown("#### 🎯 Interests & Goals")
        user_interests = st.text_area(
            "What do you want to learn?",
            value=st.session_state.user_profile["interests"],
            help="e.g., web development, data science, machine learning, career change",
            placeholder="I want to learn..."
        )
        
        # User background
        st.markdown("#### 📚 Background & Experience")
        user_background = st.text_area(
            "Tell us about your background",
            value=st.session_state.user_profile["background"],
            help="e.g., computer science student, marketing professional, complete beginner",
            placeholder="I am a..."
        )
        
        # Skill level
        st.markdown("#### 📊 Current Skill Level")
        skill_level = st.selectbox(
            "What's your current skill level?",
            options=["", "Beginner", "Intermediate", "Advanced"],
            index=0 if not st.session_state.user_profile["skill_level"] else 
                  ["", "Beginner", "Intermediate", "Advanced"].index(st.session_state.user_profile["skill_level"]),
            help="This helps us recommend appropriate courses"
        )
        
        # Update profile button
        if st.button("💾 Update Profile", use_container_width=True):
            st.session_state.user_profile = {
                "interests": user_interests,
                "background": user_background,
                "skill_level": skill_level
            }
            st.success("✅ Profile updated successfully!")
            st.balloons()
        
        st.markdown("---")
        
        # Quick course search
        st.markdown("### 🔍 Quick Course Search")
        search_query = st.text_input(
            "Search courses directly:",
            placeholder="e.g., Python, machine learning, web development"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            search_button = st.button("🔍 Search", use_container_width=True)
        with col2:
            if st.button("🎲 Random", use_container_width=True):
                import random
                random_courses = random.sample(st.session_state.rag_system.courses, 3)
                st.markdown('<div class="search-results">', unsafe_allow_html=True)
                st.markdown("#### 🎲 Random Course Discovery:")
                for course in random_courses:
                    with st.expander(f"📚 {course['title']}"):
                        display_course_card(course)
                st.markdown('</div>', unsafe_allow_html=True)
        
        if search_button and search_query:
            with st.spinner("Searching courses..."):
                results = st.session_state.rag_system.search_courses(search_query, top_k=5)
                if results:
                    st.markdown('<div class="search-results">', unsafe_allow_html=True)
                    st.markdown("#### 🎯 Search Results:")
                    for course in results:
                        with st.expander(f"📚 {course['title']} ({course['similarity_score']:.2f})"):
                            display_course_card(course)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Add to search history
                    if search_query not in st.session_state.search_history:
                        st.session_state.search_history.append(search_query)
                        if len(st.session_state.search_history) > 5:
                            st.session_state.search_history.pop(0)
                else:
                    st.info("🔍 No courses found. Try different keywords!")
        
        # Search history
        if st.session_state.search_history:
            st.markdown("#### 📝 Recent Searches")
            for query in reversed(st.session_state.search_history[-3:]):
                if st.button(f"🔄 {query}", key=f"history_{query}"):
                    results = st.session_state.rag_system.search_courses(query, top_k=3)
                    if results:
                        st.markdown('<div class="search-results">', unsafe_allow_html=True)
                        st.markdown(f"#### 🔄 Results for '{query}':")
                        for course in results:
                            with st.expander(f"📚 {course['title']}"):
                                display_course_card(course)
                        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Action buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.conversation_history = []
                st.success("Chat cleared!")
                st.rerun()
        
        with col2:
            if st.button("🔄 Reset All", use_container_width=True):
                st.session_state.conversation_history = []
                st.session_state.user_profile = {"interests": "", "background": "", "skill_level": ""}
                st.session_state.search_history = []
                st.success("Everything reset!")
                st.rerun()
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 💬 Chat with Your Course Advisor")
        
        # Display conversation history
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        if st.session_state.conversation_history:
            for i, message in enumerate(st.session_state.conversation_history):
                if message["role"] == "user":
                    st.markdown(f"""
                    <div class="chat-message user-message">
                        <strong>👤 You:</strong><br>{message["content"]}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="chat-message bot-message">
                        <strong>🤖 Course Advisor:</strong><br>{message["content"]}
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align: center; padding: 40px; color: #666;">
                <h3>👋 Start a conversation!</h3>
                <p>Ask me about courses, learning paths, or career recommendations.</p>
                <p><em>Try: "I want to learn Python programming" or "Recommend data science courses"</em></p>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Chat input
        st.markdown('<div class="input-container">', unsafe_allow_html=True)
        with st.form(key="chat_form", clear_on_submit=True):
            user_input = st.text_input(
                "Type your message here...", 
                key="user_input",
                placeholder="Ask me about courses, learning paths, or career advice..."
            )
            
            col_send, col_rec, col_help = st.columns([1, 1, 1])
            
            with col_send:
                send_button = st.form_submit_button("📤 Send", use_container_width=True)
            
            with col_rec:
                rec_button = st.form_submit_button("💡 Get Recommendations", use_container_width=True)
            
            with col_help:
                help_button = st.form_submit_button("❓ Help", use_container_width=True)
            
            if rec_button:
                user_input = "Can you recommend some courses for me based on my profile?"
                send_button = True
            
            if help_button:
                user_input = "How can you help me find the right courses?"
                send_button = True
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Process user input
        if send_button and user_input:
            # Add user message to history
            st.session_state.conversation_history.append({
                "role": "user",
                "content": user_input
            })
            
            # Generate response
            with st.spinner("🤔 Thinking..."):
                try:
                    response = st.session_state.chatbot.generate_response(
                        user_message=user_input,
                        user_interests=st.session_state.user_profile["interests"],
                        user_background=st.session_state.user_profile["background"],
                        skill_level=st.session_state.user_profile["skill_level"]
                    )
                    
                    # Add bot response to history
                    st.session_state.conversation_history.append({
                        "role": "assistant",
                        "content": response
                    })
                    
                except Exception as e:
                    error_message = f"❌ Sorry, I encountered an error: {str(e)}"
                    st.session_state.conversation_history.append({
                        "role": "assistant",
                        "content": error_message
                    })
            
            # Rerun to show the new messages
            st.rerun()
    
    with col2:
        st.markdown("### ⭐ Featured Courses")
        
        # Featured courses (simplified)
        if st.session_state.rag_system:
            courses = st.session_state.rag_system.courses
            featured_courses = sorted(courses, key=lambda x: x['rating'], reverse=True)[:3]
            
            for course in featured_courses:
                st.markdown(f"""
                <div class="featured-course">
                    <h4>{course['title']}</h4>
                    <p><strong>{course['category']}</strong> - {course['difficulty']}</p>
                    <p>⏰ {course['duration']}</p>
                    <p style="font-size: 0.9em; margin-top: 10px;">
                        {course['description'][:120]}...
                    </p>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Search suggestions
        st.markdown("#### 💡 Search Suggestions")
        display_search_suggestions()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                color: white; border-radius: 15px; margin-top: 40px;">
        <h3>🎓 Course Recommendation Bot</h3>
        <p style="font-size: 1.1em; margin: 15px 0;">
            Powered by AI and RAG Technology for Personalized Learning
        </p>
        <p style="font-size: 0.9em; opacity: 0.9;">
            🚀 Get personalized course recommendations based on your goals and background<br>
            🔍 Search through our comprehensive course database<br>
            💬 Chat with AI for intelligent learning guidance
        </p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()