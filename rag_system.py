import json
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
import faiss
from typing import List, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CourseRAGSystem:
    def __init__(self, course_data_path: str = "course_data.json"):
        """
        Initialize the RAG system with course data and embeddings
        
        Args:
            course_data_path: Path to the JSON file containing course data
        """
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.courses = []
        self.course_embeddings = None
        self.index = None
        self.course_data_path = course_data_path
        
        # Load and initialize the system
        self.load_courses()
        self.create_embeddings()
        self.build_index()
    
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
        return ' '.join(text_parts)
    
    def create_embeddings(self) -> None:
        """Create embeddings for all courses"""
        try:
            course_texts = [self.create_course_text(course) for course in self.courses]
            self.course_embeddings = self.model.encode(course_texts)
            logger.info(f"Created embeddings for {len(course_texts)} courses")
        except Exception as e:
            logger.error(f"Error creating embeddings: {e}")
            raise
    
    def build_index(self) -> None:
        """Build FAISS index for similarity search"""
        try:
            if self.course_embeddings is not None:
                dimension = self.course_embeddings.shape[1]
                self.index = faiss.IndexFlatIP(dimension)  # Inner product for similarity
                
                # Normalize embeddings for cosine similarity
                faiss.normalize_L2(self.course_embeddings)
                self.index.add(self.course_embeddings.astype('float32'))
                
                logger.info(f"Built FAISS index with {self.index.ntotal} vectors")
        except Exception as e:
            logger.error(f"Error building index: {e}")
            raise
    
    def search_courses(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for courses based on a query
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of matching courses with similarity scores
        """
        try:
            # Encode the query
            query_embedding = self.model.encode([query])
            faiss.normalize_L2(query_embedding)
            
            # Search in the index
            scores, indices = self.index.search(query_embedding.astype('float32'), top_k)
            
            # Prepare results
            results = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx < len(self.courses):
                    course = self.courses[idx].copy()
                    course['similarity_score'] = float(score)
                    course['rank'] = i + 1
                    results.append(course)
            
            return results
        
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
