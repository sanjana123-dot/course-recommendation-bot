import json
import re
from typing import List, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleCourseRAGSystem:
    def __init__(self, course_data_path: str = "course_data.json"):
        """
        Initialize the simple RAG system with course data
        
        Args:
            course_data_path: Path to the JSON file containing course data
        """
        self.courses = []
        self.course_data_path = course_data_path
        
        # Load courses
        self.load_courses()
    
    def load_courses(self) -> None:
        """Load courses from JSON file"""
        try:
            with open(self.course_data_path, 'r') as f:
                data = json.load(f)
                self.courses = data['courses']
            logger.info(f"Loaded {len(self.courses)} courses")
        except FileNotFoundError:
            logger.error(f"Course data file not found: {self.course_data_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON file: {e}")
            raise
    
    def create_course_text(self, course: Dict[str, Any]) -> str:
        """
        Create a searchable text representation of a course
        
        Args:
            course: Course dictionary
            
        Returns:
            Combined text representation of the course
        """
        text_parts = [
            course['title'],
            course['description'],
            course['category'],
            course['difficulty'],
            ' '.join(course['skills']),
            course['prerequisites']
        ]
        return ' '.join(text_parts).lower()
    
    def simple_search_score(self, query: str, course_text: str) -> float:
        """
        Calculate a simple search score based on keyword matching
        
        Args:
            query: Search query
            course_text: Course text to search in
            
        Returns:
            Score between 0 and 1
        """
        query_words = set(re.findall(r'\b\w+\b', query.lower()))
        course_words = set(re.findall(r'\b\w+\b', course_text.lower()))
        
        if not query_words:
            return 0.0
        
        # Calculate intersection
        common_words = query_words.intersection(course_words)
        score = len(common_words) / len(query_words)
        
        # Boost score for exact phrase matches
        if query.lower() in course_text.lower():
            score += 0.3
        
        return min(score, 1.0)
    
    def search_courses(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for courses based on a query using simple keyword matching
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of matching courses with similarity scores
        """
        try:
            results = []
            
            for course in self.courses:
                course_text = self.create_course_text(course)
                score = self.simple_search_score(query, course_text)
                
                if score > 0:
                    course_copy = course.copy()
                    course_copy['similarity_score'] = score
                    results.append(course_copy)
            
            # Sort by score and return top_k
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            # Add rank
            for i, course in enumerate(results[:top_k]):
                course['rank'] = i + 1
            
            return results[:top_k]
        
        except Exception as e:
            logger.error(f"Error searching courses: {e}")
            return []
    
    def get_course_by_id(self, course_id: str) -> Dict[str, Any]:
        """
        Get a specific course by ID
        
        Args:
            course_id: Course identifier
            
        Returns:
            Course dictionary or None if not found
        """
        for course in self.courses:
            if course['id'] == course_id:
                return course
        return None
    
    def filter_courses(self, 
                      category: str = None, 
                      difficulty: str = None, 
                      skills: List[str] = None) -> List[Dict[str, Any]]:
        """
        Filter courses by specific criteria
        
        Args:
            category: Course category
            difficulty: Course difficulty level
            skills: List of required skills
            
        Returns:
            List of filtered courses
        """
        filtered_courses = self.courses.copy()
        
        if category:
            filtered_courses = [c for c in filtered_courses 
                              if c['category'].lower() == category.lower()]
        
        if difficulty:
            filtered_courses = [c for c in filtered_courses 
                              if c['difficulty'].lower() == difficulty.lower()]
        
        if skills:
            skills_lower = [skill.lower() for skill in skills]
            filtered_courses = [c for c in filtered_courses 
                              if any(skill.lower() in skills_lower 
                                   for skill in c['skills'])]
        
        return filtered_courses
    
    def get_recommendations(self, 
                          user_interests: str, 
                          user_background: str = "", 
                          skill_level: str = "", 
                          top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Get personalized course recommendations
        
        Args:
            user_interests: User's interests and goals
            user_background: User's background and experience
            skill_level: User's skill level (Beginner, Intermediate, Advanced)
            top_k: Number of recommendations to return
            
        Returns:
            List of recommended courses
        """
        # Combine user inputs into a search query
        query_parts = [user_interests]
        if user_background:
            query_parts.append(user_background)
        if skill_level:
            query_parts.append(skill_level)
        
        query = ' '.join(query_parts)
        
        # Search for courses
        recommendations = self.search_courses(query, top_k * 2)  # Get more results to filter
        
        # Filter by skill level if specified
        if skill_level and skill_level.lower() in ['beginner', 'intermediate', 'advanced']:
            recommendations = [course for course in recommendations 
                             if course['difficulty'].lower() == skill_level.lower()]
        
        # Return top_k results
        return recommendations[:top_k]