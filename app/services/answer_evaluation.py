"""
Answer evaluation and processing service
"""

import re
import json
from typing import Dict, List, Optional, Tuple
from app.core.logger import get_logger
from app.tools.agent_tools import agent_tools

logger = get_logger(__name__)

class AnswerEvaluationService:
    """Service for evaluating user answers against correct answers"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    def extract_questions_from_content(self, content: str) -> Dict[str, Dict]:
        """Extract questions and correct answers from activity content"""
        questions = {}
        
        # Pattern to match different question types
        patterns = {
            'mcq': r'(\d+\.?\s*[A-Z][^A-Z]*?)(?=\d+\.?\s*[A-Z]|\Z)',
            'true_false': r'(\d+\.?\s*True/False[^?]*?\?)',
            'short_answer': r'(\d+\.?\s*[^?]*?\?)'
        }
        
        # Extract multiple choice questions
        mcq_matches = re.findall(patterns['mcq'], content, re.IGNORECASE | re.DOTALL)
        for i, match in enumerate(mcq_matches):
            question_id = f"q{i+1}"
            questions[question_id] = {
                "question": match.strip(),
                "type": "mcq",
                "correct_answer": self._extract_correct_answer(match),
                "options": self._extract_options(match)
            }
        
        # Extract true/false questions
        tf_matches = re.findall(patterns['true_false'], content, re.IGNORECASE | re.DOTALL)
        for i, match in enumerate(tf_matches):
            question_id = f"q{len(questions)+1}"
            questions[question_id] = {
                "question": match.strip(),
                "type": "true_false",
                "correct_answer": self._extract_tf_answer(match),
                "options": ["True", "False"]
            }
        
        # Extract short answer questions
        sa_matches = re.findall(patterns['short_answer'], content, re.IGNORECASE | re.DOTALL)
        for i, match in enumerate(sa_matches):
            question_id = f"q{len(questions)+1}"
            questions[question_id] = {
                "question": match.strip(),
                "type": "short_answer",
                "correct_answer": self._extract_short_answer(match),
                "options": []
            }
        
        return questions
    
    def _extract_correct_answer(self, question_text: str) -> str:
        """Extract correct answer from question text"""
        # Look for patterns like "Answer: A" or "Correct: B"
        answer_patterns = [
            r'Answer:\s*([A-D])',
            r'Correct:\s*([A-D])',
            r'Answer\s*([A-D])',
            r'Correct\s*([A-D])'
        ]
        
        for pattern in answer_patterns:
            match = re.search(pattern, question_text, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        
        # If no explicit answer found, try to infer from context
        return self._infer_correct_answer(question_text)
    
    def _extract_options(self, question_text: str) -> List[str]:
        """Extract answer options from question text"""
        options = []
        option_pattern = r'[A-D]\)\s*([^\n]+)'
        matches = re.findall(option_pattern, question_text)
        
        for match in matches:
            options.append(match.strip())
        
        return options
    
    def _extract_tf_answer(self, question_text: str) -> str:
        """Extract correct true/false answer"""
        # Look for patterns indicating correct answer
        if re.search(r'True', question_text, re.IGNORECASE):
            return "True"
        elif re.search(r'False', question_text, re.IGNORECASE):
            return "False"
        return "Unknown"
    
    def _extract_short_answer(self, question_text: str) -> str:
        """Extract expected short answer"""
        # For short answers, we'll need to use AI to generate expected answers
        # For now, return a placeholder
        return "Expected answer based on question context"
    
    def _infer_correct_answer(self, question_text: str) -> str:
        """Infer correct answer based on question context"""
        # Simple heuristics for inferring correct answers
        if "simplest" in question_text.lower() or "basic" in question_text.lower():
            return "A"  # Usually the simplest answer is A
        elif "complex" in question_text.lower() or "advanced" in question_text.lower():
            return "D"  # Usually the most complex answer is D
        else:
            return "B"  # Default to B as most common correct answer
    
    async def extract_answers_using_llm(self, user_message: str, question_mappings: Dict) -> Dict[str, str]:
        """Use LLM to dynamically extract answers from any format"""
        try:
            # Create a prompt that includes all available questions for context
            questions_context = ""
            for q_id, q_data in question_mappings.items():
                question_text = q_data.get("question", "")[:100]  # Truncate for context
                questions_context += f"{q_id}: {question_text}\n"
            
            extraction_prompt = f"""
            Analyze this user's answer submission and extract the answers for each question.

            **Available Questions:**
            {questions_context}

            **User's Answer Submission:**
            {user_message}

            **Instructions:**
            1. Identify all answers in the user's submission
            2. Map each answer to the correct question ID (q1, q2, q3, etc.)
            3. Normalize answers to uppercase (A, B, C, D, TRUE, FALSE)
            4. Handle any format: numbered lists, bullet points, plain text, etc.
            5. For missing questions, skip them (don't guess)

            **Expected Output Format:**
            Return a JSON object with question IDs as keys and answers as values:
            {{
                "q1": "A",
                "q2": "B", 
                "q3": "TRUE",
                "q4": "FALSE",
                "q5": "C"
            }}

            **Examples of formats to handle:**
            - "1. A 2. B 3. C" → {{"q1": "A", "q2": "B", "q3": "C"}}
            - "A, B, C, D" → {{"q1": "A", "q2": "B", "q3": "C", "q4": "D"}}
            - "1. b 2. b 3. b 4. d 5. b" → {{"q1": "B", "q2": "B", "q3": "B", "q4": "D", "q5": "B"}}
            - "True, False, True, False" → {{"q1": "TRUE", "q2": "FALSE", "q3": "TRUE", "q4": "FALSE"}}

            Return only the JSON object:
            """
            
            # Call LLM for extraction
            from app.config.agent_config import get_chat_completion_config
            config_settings = get_chat_completion_config()
            
            response = await agent_tools._chat_completion(
                prompt=extraction_prompt,
                temperature=0.1,
                max_tokens=500,
                json_mode=True
            )
            
            # Parse the LLM response
            extracted_answers = {}
            if "response" in response and "text" in response["response"]:
                try:
                    extracted_answers = json.loads(response["response"]["text"])
                except json.JSONDecodeError:
                    self.logger.error("Failed to parse LLM extraction result as JSON")
                    extracted_answers = {}
            elif "response" in response:
                # Handle case where response is already a dict
                extracted_answers = response["response"]
            
            # Validate and normalize answers
            validated_answers = {}
            for q_id, answer in extracted_answers.items():
                if q_id in question_mappings:
                    # Normalize answer
                    normalized_answer = str(answer).strip().upper()
                    if normalized_answer in ["A", "B", "C", "D", "TRUE", "FALSE"]:
                        validated_answers[q_id] = normalized_answer
            
            return validated_answers
            
        except Exception as e:
            self.logger.error(f"Error in LLM answer extraction: {e}")
            return {}
    
    def extract_user_answer(self, user_message: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract question ID and answer from user message (legacy method)"""
        # Pattern to match "answer to question X is Y"
        patterns = [
            r'answer\s+to\s+question\s+(\d+)\s+is\s+([A-D])',
            r'question\s+(\d+)\s+answer\s+is\s+([A-D])',
            r'q(\d+)\s+answer\s+is\s+([A-D])',
            r'(\d+)\.\s*([A-D])',
            r'answer\s+(\d+)\s+([A-D])'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, user_message, re.IGNORECASE)
            if match:
                question_id = f"q{match.group(1)}"
                answer = match.group(2).upper()
                return question_id, answer
        
        # Try to extract just the answer if question number is implied
        answer_match = re.search(r'\b([A-D])\b', user_message.upper())
        if answer_match:
            return None, answer_match.group(1)
        
        return None, None
    
    async def process_answers_dynamically(self, user_message: str, session_data: Dict) -> Dict:
        """Process answers using LLM for dynamic format handling - just store for context"""
        question_mappings = session_data.get('question_mappings', {})
        
        if not question_mappings:
            return {"error": "No questions available for this session"}
        
        # Use LLM to extract answers from any format
        extracted_answers = await self.extract_answers_using_llm(user_message, question_mappings)
        
        if not extracted_answers:
            return {"error": "No valid answers found in the provided format"}
        
        results = {
            "processed_answers": extracted_answers,
            "total_answers": len(extracted_answers),
            "message": "Answers stored successfully for context"
        }
        
        return results
    
    def store_answers_for_context(self, session_data: Dict, new_answers: Dict[str, str]) -> Dict:
        """Store answers in session data for LLM context without evaluation"""
        # Update user answers
        if 'user_answers' not in session_data:
            session_data['user_answers'] = {}
        
        # Store new answers
        for question_id, answer in new_answers.items():
            session_data['user_answers'][question_id] = answer
        
        # Update progress data
        if 'progress_data' not in session_data:
            session_data['progress_data'] = {
                'completed_questions': [],
                'skipped_questions': [],
                'current_question': 1
            }
        
        # Add completed questions
        for question_id in new_answers.keys():
            if question_id not in session_data['progress_data']['completed_questions']:
                session_data['progress_data']['completed_questions'].append(question_id)
        
        # Update total questions count
        session_data['total_questions'] = len(session_data.get('question_mappings', {}))
        session_data['answered_questions'] = len(session_data['user_answers'])
        
        return session_data

# Global instance
answer_evaluation_service = AnswerEvaluationService() 