from typing import Dict, List, Any, Optional, Tuple
from uuid import UUID
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import AzureChatOpenAI
from sqlalchemy.orm import Session
from datetime import datetime
import json
import re

from app.core.logger import get_logger
from app.core.azure_config import load_azure_config
from app.models.evaluation import (
    EvaluationResult, EvaluationType, EvaluationStatus, 
    QuizQuestion, LearningProgress
)
from app.models.activity import Activity
from app.models.user import User
from app.models.activity_session import ActivitySession
from app.models.document import Document as DocumentModel
from app.services.pgvector_service import PgVectorService

logger = get_logger(__name__)

# Load Azure configuration
azure_config = load_azure_config()
llm = AzureChatOpenAI(
    openai_api_version=azure_config.api_version,
    azure_deployment=azure_config.deployment,
    azure_endpoint=azure_config.endpoint,
    api_key=azure_config.api_key,
    temperature=0.3,
    max_tokens=2000
)

class EvaluationAgent:
    def __init__(self, db: Session):
        self.db = db
        self.pgvector_service = PgVectorService()
        self.workflow = self._create_workflow()
        
        # Define evaluation metrics and their weights
        self.evaluation_metrics = {
            "quiz": {
                "accuracy": 0.4,
                "difficulty_distribution": 0.2,
                "response_time": 0.1,
                "concept_mastery": 0.3
            },
            "progress": {
                "completion_rate": 0.3,
                "engagement_time": 0.2,
                "session_frequency": 0.2,
                "learning_consistency": 0.3
            },
            "document": {
                "comprehension_depth": 0.4,
                "concept_retention": 0.3,
                "application_ability": 0.3
            },
            "reflection": {
                "self_awareness": 0.3,
                "critical_thinking": 0.4,
                "learning_insights": 0.3
            },
            "project": {
                "creativity": 0.2,
                "technical_skills": 0.3,
                "problem_solving": 0.3,
                "presentation": 0.2
            },
            "presentation": {
                "communication": 0.3,
                "content_quality": 0.3,
                "audience_engagement": 0.2,
                "technical_delivery": 0.2
            }
        }

    def _create_workflow(self) -> StateGraph:
        """Create the evaluation workflow using LangGraph"""
        workflow = StateGraph(dict)
        
        # Add nodes
        workflow.add_node("classify_input", self._classify_input)
        workflow.add_node("gather_context", self._gather_context)
        workflow.add_node("evaluate", self._evaluate_based_on_type)
        workflow.add_node("analyze_rag", self._analyze_rag_context)
        workflow.add_node("generate_report", self._generate_report)
        
        # Define the workflow
        workflow.set_entry_point("classify_input")
        workflow.add_edge("classify_input", "gather_context")
        workflow.add_edge("gather_context", "evaluate")
        workflow.add_edge("evaluate", "analyze_rag")
        workflow.add_edge("analyze_rag", "generate_report")
        workflow.add_edge("generate_report", END)
        
        return workflow.compile()

    async def _classify_input(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Dynamically classify the input type using LLM"""
        prompt = ChatPromptTemplate.from_template("""
        You are an expert academic evaluator. Based on the context below, classify the academic input type.

        Available categories:
        - "quiz": Multiple choice, true/false, or short answer assessments
        - "progress": Learning progress analysis, study patterns, completion rates
        - "document": Document understanding, reading comprehension, material analysis
        - "reflection": Self-reflection, learning insights, personal growth analysis
        - "project": Project work, assignments, creative outputs
        - "presentation": Oral presentations, demonstrations, public speaking
        - "comprehensive": Multi-faceted evaluation combining multiple types

        Context: {context}
        User ID: {user_id}
        Activity ID: {activity_id}
        Session ID: {session_id}

        Consider the following indicators:
        - Keywords in the context
        - Type of data available
        - User's intent and request
        - Activity type and structure

        Respond with exactly one category from the list above.
        """)
        
        context = state.get("chat_context", "")
        user_id = state.get("user_id", "")
        activity_id = state.get("activity_id", "")
        session_id = state.get("session_id", "")
        
        try:
            response = await llm.ainvoke(
                prompt.format(
                    context=context,
                    user_id=user_id,
                    activity_id=activity_id,
                    session_id=session_id or "none"
                )
            )
            
            # Clean and validate the response
            evaluation_type = response.content.strip().lower()
            valid_types = ["quiz", "progress", "document", "reflection", "project", "presentation", "comprehensive"]
            
            if evaluation_type not in valid_types:
                logger.warning(f"Invalid evaluation type '{evaluation_type}', defaulting to comprehensive")
                evaluation_type = "comprehensive"
            
            state["evaluation_type"] = evaluation_type
            logger.info(f"Classified input as: {evaluation_type}")
            
        except Exception as e:
            logger.error(f"Error in input classification: {e}")
            state["evaluation_type"] = "comprehensive"
        
        return state

    async def _gather_context(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Gather relevant context data for evaluation"""
        user_id = state.get("user_id")
        activity_id = state.get("activity_id")
        session_id = state.get("session_id")
        evaluation_type = state.get("evaluation_type")
        
        try:
            # Get user and activity data
            user = self.db.query(User).filter(User.id == user_id).first()
            activity = self.db.query(Activity).filter(Activity.id == activity_id).first()
            
            # Gather context based on evaluation type
            context_data = {
                "user": user,
                "activity": activity,
                "evaluation_type": evaluation_type
            }
            
            if evaluation_type == "quiz":
                # Get quiz data from session or chat context
                context_data["quiz_data"] = await self._extract_quiz_data(state)
                
            elif evaluation_type == "progress":
                # Get learning progress data
                context_data["progress_data"] = await self._extract_progress_data(user_id, activity_id)
                
            elif evaluation_type == "document":
                # Get document data
                context_data["document_data"] = await self._extract_document_data(activity_id)
                
            elif evaluation_type == "reflection":
                # Get reflection data
                context_data["reflection_data"] = await self._extract_reflection_data(state)
                
            elif evaluation_type == "project":
                # Get project data
                context_data["project_data"] = await self._extract_project_data(state)
                
            elif evaluation_type == "presentation":
                # Get presentation data
                context_data["presentation_data"] = await self._extract_presentation_data(state)
            
            state["context_data"] = context_data
            logger.info(f"Gathered context for {evaluation_type} evaluation")
            
        except Exception as e:
            logger.error(f"Error gathering context: {e}")
            state["context_data"] = {}
        
        return state

    async def _evaluate_based_on_type(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Route to appropriate evaluation method based on type"""
        evaluation_type = state.get("evaluation_type")
        
        try:
            if evaluation_type == "quiz":
                return await self._evaluate_quiz(state)
            elif evaluation_type == "progress":
                return await self._evaluate_progress(state)
            elif evaluation_type == "document":
                return await self._evaluate_document(state)
            elif evaluation_type == "reflection":
                return await self._evaluate_reflection(state)
            elif evaluation_type == "project":
                return await self._evaluate_project(state)
            elif evaluation_type == "presentation":
                return await self._evaluate_presentation(state)
            else:
                return await self._evaluate_comprehensive(state)
                
        except Exception as e:
            logger.error(f"Error in evaluation: {e}")
            state["evaluation_error"] = str(e)
            return state

    async def _evaluate_quiz(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate quiz responses with chain-of-thought reasoning"""
        quiz_data = state.get("context_data", {}).get("quiz_data", [])
        
        if not quiz_data:
            # Mock quiz data for demonstration
            quiz_data = [
                {
                    "question": "What is the capital of France?",
                    "user_answer": "Paris",
                    "correct_answer": "Paris",
                    "difficulty": "easy",
                    "response_time": 15
                },
                {
                    "question": "What is 2 + 2?",
                    "user_answer": "4",
                    "correct_answer": "4",
                    "difficulty": "easy",
                    "response_time": 8
                },
                {
                    "question": "What is the square root of 16?",
                    "user_answer": "5",
                    "correct_answer": "4",
                    "difficulty": "medium",
                    "response_time": 25
                }
            ]
        
        # Calculate basic metrics
        total_questions = len(quiz_data)
        correct_answers = sum(1 for q in quiz_data if q["user_answer"] == q["correct_answer"])
        accuracy = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
        
        # Calculate difficulty breakdown
        difficulty_scores = {"easy": 0, "medium": 0, "hard": 0}
        difficulty_counts = {"easy": 0, "medium": 0, "hard": 0}
        response_times = []
        
        for question in quiz_data:
            difficulty = question.get("difficulty", "medium")
            difficulty_counts[difficulty] += 1
            response_times.append(question.get("response_time", 0))
            
            if question["user_answer"] == question["correct_answer"]:
                difficulty_scores[difficulty] += 1
        
        difficulty_breakdown = {}
        for difficulty in difficulty_scores:
            if difficulty_counts[difficulty] > 0:
                difficulty_breakdown[difficulty] = (difficulty_scores[difficulty] / difficulty_counts[difficulty]) * 100
            else:
                difficulty_breakdown[difficulty] = 0
        
        # Chain-of-thought reasoning
        prompt = ChatPromptTemplate.from_template("""
        Analyze this quiz attempt step by step:

        Quiz Data: {quiz_data}
        Accuracy: {accuracy}%
        Difficulty Breakdown: {difficulty_breakdown}
        Average Response Time: {avg_response_time} seconds

        Provide detailed reasoning for:
        1. What patterns do you observe in the student's performance?
        2. What are the student's strengths and weaknesses?
        3. What specific areas need improvement?
        4. How does the response time relate to accuracy?
        5. What learning recommendations would you make?

        Format your response as structured analysis with clear sections.
        """)
        
        try:
            reasoning = await llm.ainvoke(
                prompt.format(
                    quiz_data=json.dumps(quiz_data, indent=2),
                    accuracy=accuracy,
                    difficulty_breakdown=json.dumps(difficulty_breakdown),
                    avg_response_time=sum(response_times) / len(response_times) if response_times else 0
                )
            )
            
            # Calculate weighted score using metrics
            metrics = self.evaluation_metrics["quiz"]
            weighted_score = (
                accuracy * metrics["accuracy"] +
                (sum(difficulty_breakdown.values()) / len(difficulty_breakdown)) * metrics["difficulty_distribution"] +
                (100 - min(sum(response_times) / len(response_times), 60)) * metrics["response_time"] +
                accuracy * metrics["concept_mastery"]  # Using accuracy as proxy for concept mastery
            )
            
            state["quiz_results"] = {
                "accuracy": accuracy,
                "difficulty_breakdown": difficulty_breakdown,
                "average_response_time": sum(response_times) / len(response_times) if response_times else 0,
                "weighted_score": weighted_score,
                "reasoning": reasoning.content,
                "questions": quiz_data,
                "metrics_used": metrics
            }
            
        except Exception as e:
            logger.error(f"Error in quiz evaluation reasoning: {e}")
            state["quiz_results"] = {
                "accuracy": accuracy,
                "difficulty_breakdown": difficulty_breakdown,
                "reasoning": "Error in detailed analysis",
                "questions": quiz_data
            }
        
        return state

    async def _evaluate_progress(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate learning progress with comprehensive analysis"""
        user_id = state.get("user_id")
        activity_id = state.get("activity_id")
        
        try:
            # Get learning progress data
            progress_data = state.get("context_data", {}).get("progress_data", {})
            
            if not progress_data:
                # Mock progress data
                progress_data = {
                    "sessions": [
                        {"status": "completed", "time_spent": 1800, "date": "2024-01-10"},
                        {"status": "completed", "time_spent": 2100, "date": "2024-01-11"},
                        {"status": "in_progress", "time_spent": 900, "date": "2024-01-12"}
                    ],
                    "total_interactions": 25,
                    "questions_asked": 12,
                    "help_requests": 3
                }
            
            # Calculate metrics
            sessions = progress_data.get("sessions", [])
            completion_rate = len([s for s in sessions if s.get("status") == "completed"]) / len(sessions) if sessions else 0
            total_time = sum(s.get("time_spent", 0) for s in sessions)
            avg_session_time = total_time / len(sessions) if sessions else 0
            
            # Chain-of-thought reasoning
            prompt = ChatPromptTemplate.from_template("""
            Analyze this student's learning progress:

            Progress Data: {progress_data}
            Completion Rate: {completion_rate}%
            Total Time Spent: {total_time} seconds
            Average Session Time: {avg_session_time} seconds

            Provide detailed analysis of:
            1. Learning consistency and patterns
            2. Engagement level and time management
            3. Study habits and effectiveness
            4. Areas of improvement
            5. Recommendations for better learning outcomes

            Consider factors like session frequency, time distribution, and engagement quality.
            """)
            
            reasoning = await llm.ainvoke(
                prompt.format(
                    progress_data=json.dumps(progress_data, indent=2),
                    completion_rate=completion_rate * 100,
                    total_time=total_time,
                    avg_session_time=avg_session_time
                )
            )
            
            # Calculate weighted score
            metrics = self.evaluation_metrics["progress"]
            weighted_score = (
                completion_rate * 100 * metrics["completion_rate"] +
                min(total_time / 3600, 10) * 10 * metrics["engagement_time"] +  # Normalize to 0-100
                min(len(sessions) / 10, 1) * 100 * metrics["session_frequency"] +
                completion_rate * 100 * metrics["learning_consistency"]
            )
            
            state["progress_results"] = {
                "completion_rate": completion_rate,
                "total_time_spent": total_time,
                "average_session_time": avg_session_time,
                "session_count": len(sessions),
                "weighted_score": weighted_score,
                "reasoning": reasoning.content,
                "metrics_used": metrics
            }
            
        except Exception as e:
            logger.error(f"Error in progress evaluation: {e}")
            state["progress_results"] = {
                "completion_rate": 0,
                "reasoning": "Error in progress analysis"
            }
        
        return state

    async def _evaluate_document(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate document understanding using RAG"""
        activity_id = state.get("activity_id")
        
        try:
            # Get documents for this activity
            documents = self.db.query(DocumentModel).filter(
                DocumentModel.activity_id == activity_id,
                DocumentModel.is_processed == True
            ).all()
            
            # Use RAG to analyze document understanding
            document_analysis = []
            total_chunks = 0
            
            for doc in documents:
                # Search for relevant chunks using pgvector
                doc_chunks = await self.pgvector_service.search_similar_chunks(
                    query="key concepts main ideas understanding",
                    activity_id=str(activity_id),
                    document_ids=[str(doc.id)],
                    k=5
                )
                
                total_chunks += len(doc_chunks)
                
                if doc_chunks:
                    # Analyze understanding using LLM
                    prompt = ChatPromptTemplate.from_template("""
                    Analyze the student's understanding of this document content:

                    Document: {doc_name}
                    Content Chunks: {chunks}

                    Evaluate:
                    1. Comprehension depth (1-10)
                    2. Key concepts identified
                    3. Understanding gaps
                    4. Application potential
                    5. Suggested follow-up questions

                    Provide a structured analysis with specific insights.
                    """)
                    
                    chunks_text = "\n\n".join([c.page_content for c in doc_chunks])
                    analysis = await llm.ainvoke(
                        prompt.format(
                            doc_name=doc.name,
                            chunks=chunks_text
                        )
                    )
                    
                    document_analysis.append({
                        "document_id": str(doc.id),
                        "document_name": doc.name,
                        "chunks_analyzed": len(doc_chunks),
                        "analysis": analysis.content
                    })
            
            # Overall document understanding score
            comprehension_score = min(total_chunks * 10, 100)  # Mock score based on chunks analyzed
            
            # Calculate weighted score
            metrics = self.evaluation_metrics["document"]
            weighted_score = (
                comprehension_score * metrics["comprehension_depth"] +
                comprehension_score * metrics["concept_retention"] +
                comprehension_score * metrics["application_ability"]
            )
            
            state["document_results"] = {
                "documents_analyzed": len(documents),
                "total_chunks": total_chunks,
                "comprehension_score": comprehension_score,
                "weighted_score": weighted_score,
                "document_analysis": document_analysis,
                "metrics_used": metrics
            }
            
        except Exception as e:
            logger.error(f"Error in document evaluation: {e}")
            state["document_results"] = {
                "documents_analyzed": 0,
                "comprehension_score": 0,
                "analysis": "Error in document analysis"
            }
        
        return state

    async def _evaluate_reflection(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate reflection and self-awareness"""
        reflection_data = state.get("context_data", {}).get("reflection_data", "")
        
        if not reflection_data:
            reflection_data = "I learned that machine learning requires patience and practice. I struggled with neural networks but found supervised learning easier to understand."
        
        prompt = ChatPromptTemplate.from_template("""
        Analyze this student's reflection:

        Reflection: {reflection}

        Evaluate on a scale of 1-10:
        1. Self-awareness (understanding of own learning)
        2. Critical thinking (depth of analysis)
        3. Learning insights (valuable observations)

        Provide detailed reasoning and suggestions for improvement.
        """)
        
        try:
            analysis = await llm.ainvoke(prompt.format(reflection=reflection_data))
            
            # Mock scores based on content analysis
            self_awareness = 7
            critical_thinking = 6
            learning_insights = 8
            
            metrics = self.evaluation_metrics["reflection"]
            weighted_score = (
                self_awareness * metrics["self_awareness"] +
                critical_thinking * metrics["critical_thinking"] +
                learning_insights * metrics["learning_insights"]
            ) * 10  # Scale to 0-100
            
            state["reflection_results"] = {
                "self_awareness": self_awareness,
                "critical_thinking": critical_thinking,
                "learning_insights": learning_insights,
                "weighted_score": weighted_score,
                "analysis": analysis.content,
                "metrics_used": metrics
            }
            
        except Exception as e:
            logger.error(f"Error in reflection evaluation: {e}")
            state["reflection_results"] = {
                "weighted_score": 0,
                "analysis": "Error in reflection analysis"
            }
        
        return state

    async def _evaluate_project(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate project work"""
        project_data = state.get("context_data", {}).get("project_data", {})
        
        if not project_data:
            project_data = {
                "title": "Machine Learning Implementation",
                "description": "Built a simple neural network for classification",
                "complexity": "medium",
                "completion": 85
            }
        
        # Mock evaluation scores
        creativity = 7
        technical_skills = 8
        problem_solving = 7
        presentation = 6
        
        metrics = self.evaluation_metrics["project"]
        weighted_score = (
            creativity * metrics["creativity"] +
            technical_skills * metrics["technical_skills"] +
            problem_solving * metrics["problem_solving"] +
            presentation * metrics["presentation"]
        ) * 10
        
        state["project_results"] = {
            "creativity": creativity,
            "technical_skills": technical_skills,
            "problem_solving": problem_solving,
            "presentation": presentation,
            "weighted_score": weighted_score,
            "project_data": project_data,
            "metrics_used": metrics
        }
        
        return state

    async def _evaluate_presentation(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate presentation skills"""
        presentation_data = state.get("context_data", {}).get("presentation_data", {})
        
        if not presentation_data:
            presentation_data = {
                "topic": "Introduction to AI",
                "duration": 15,
                "audience_feedback": "positive"
            }
        
        # Mock evaluation scores
        communication = 7
        content_quality = 8
        audience_engagement = 6
        technical_delivery = 7
        
        metrics = self.evaluation_metrics["presentation"]
        weighted_score = (
            communication * metrics["communication"] +
            content_quality * metrics["content_quality"] +
            audience_engagement * metrics["audience_engagement"] +
            technical_delivery * metrics["technical_delivery"]
        ) * 10
        
        state["presentation_results"] = {
            "communication": communication,
            "content_quality": content_quality,
            "audience_engagement": audience_engagement,
            "technical_delivery": technical_delivery,
            "weighted_score": weighted_score,
            "presentation_data": presentation_data,
            "metrics_used": metrics
        }
        
        return state

    async def _evaluate_comprehensive(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive evaluation combining multiple types"""
        # Run all evaluation types
        state = await self._evaluate_quiz(state)
        state = await self._evaluate_progress(state)
        state = await self._evaluate_document(state)
        state = await self._evaluate_reflection(state)
        
        # Combine results
        quiz_score = state.get("quiz_results", {}).get("weighted_score", 0)
        progress_score = state.get("progress_results", {}).get("weighted_score", 0)
        document_score = state.get("document_results", {}).get("weighted_score", 0)
        reflection_score = state.get("reflection_results", {}).get("weighted_score", 0)
        
        # Calculate overall score with weights
        comprehensive_score = (
            quiz_score * 0.3 +
            progress_score * 0.25 +
            document_score * 0.25 +
            reflection_score * 0.2
        )
        
        state["comprehensive_results"] = {
            "overall_score": comprehensive_score,
            "quiz_score": quiz_score,
            "progress_score": progress_score,
            "document_score": document_score,
            "reflection_score": reflection_score,
            "evaluation_complete": True
        }
        
        return state

    async def _analyze_rag_context(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze RAG context for enhanced evaluation"""
        evaluation_type = state.get("evaluation_type")
        user_id = state.get("user_id")
        activity_id = state.get("activity_id")
        
        try:
            # Search for similar evaluation patterns
            rag_query = f"evaluation patterns for {evaluation_type} type assessments"
            similar_evaluations = await self.pgvector_service.search_evaluation_similarities(
                query=rag_query,
                user_id=str(user_id),
                activity_id=str(activity_id),
                k=3
            )
            
            # Search for relevant document chunks
            doc_chunks = await self.pgvector_service.search_similar_chunks(
                query=f"evaluation criteria {evaluation_type} assessment",
                activity_id=str(activity_id),
                k=5
            )
            
            # Generate RAG-enhanced insights
            if similar_evaluations or doc_chunks:
                prompt = ChatPromptTemplate.from_template("""
                Based on similar evaluation patterns and relevant content, provide additional insights:

                Similar Evaluations: {similar_evaluations}
                Relevant Content: {doc_chunks}

                How do these patterns and content relate to the current evaluation?
                What additional considerations should be made?
                """)
                
                similar_text = "\n".join([f"Score: {score}, Content: {content[:100]}..." for content, score in similar_evaluations])
                chunks_text = "\n".join([chunk.page_content[:200] for chunk in doc_chunks])
                
                rag_insights = await llm.ainvoke(
                    prompt.format(
                        similar_evaluations=similar_text,
                        doc_chunks=chunks_text
                    )
                )
                
                state["rag_analysis"] = {
                    "similar_evaluations": len(similar_evaluations),
                    "relevant_chunks": len(doc_chunks),
                    "insights": rag_insights.content
                }
            else:
                state["rag_analysis"] = {
                    "similar_evaluations": 0,
                    "relevant_chunks": 0,
                    "insights": "No similar patterns found"
                }
                
        except Exception as e:
            logger.error(f"Error in RAG analysis: {e}")
            state["rag_analysis"] = {
                "error": str(e)
            }
        
        return state

    async def _generate_report(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive evaluation report"""
        evaluation_type = state.get("evaluation_type")
        
        # Collect all results
        results = {}
        if "quiz_results" in state:
            results["quiz"] = state["quiz_results"]
        if "progress_results" in state:
            results["progress"] = state["progress_results"]
        if "document_results" in state:
            results["document"] = state["document_results"]
        if "reflection_results" in state:
            results["reflection"] = state["reflection_results"]
        if "project_results" in state:
            results["project"] = state["project_results"]
        if "presentation_results" in state:
            results["presentation"] = state["presentation_results"]
        if "comprehensive_results" in state:
            results["comprehensive"] = state["comprehensive_results"]
        
        # Generate student-friendly summary
        prompt = ChatPromptTemplate.from_template("""
        Generate a student-friendly evaluation report based on this data:

        Evaluation Type: {evaluation_type}
        Results: {results}
        RAG Insights: {rag_insights}

        Create a comprehensive report that includes:
        1. Overall performance summary
        2. Key strengths and achievements
        3. Areas for improvement
        4. Specific recommendations
        5. Next steps for learning
        6. Encouraging and constructive tone

        Format the report in a clear, structured manner that students can easily understand.
        """)
        
        try:
            rag_insights = state.get("rag_analysis", {}).get("insights", "No additional insights available")
            
            report = await llm.ainvoke(
                prompt.format(
                    evaluation_type=evaluation_type,
                    results=json.dumps(results, indent=2),
                    rag_insights=rag_insights
                )
            )
            
            # Calculate overall score
            overall_score = 0
            if "comprehensive_results" in results:
                overall_score = results["comprehensive"]["overall_score"]
            elif evaluation_type in results:
                overall_score = results[evaluation_type].get("weighted_score", 0)
            
            final_report = {
                "evaluation_type": evaluation_type,
                "overall_score": overall_score,
                "detailed_results": results,
                "summary": report.content,
                "rag_insights": state.get("rag_analysis", {}),
                "generated_at": datetime.now().isoformat()
            }
            
            state["report"] = final_report
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            state["report"] = {
                "evaluation_type": evaluation_type,
                "error": "Error generating report",
                "overall_score": 0
            }
        
        return state

    # Helper methods for data extraction
    async def _extract_quiz_data(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract quiz data from state or generate mock data"""
        # In real implementation, extract from session or chat context
        return []

    async def _extract_progress_data(self, user_id: str, activity_id: str) -> Dict[str, Any]:
        """Extract progress data from database"""
        try:
            sessions = self.db.query(ActivitySession).filter(
                ActivitySession.user_id == user_id,
                ActivitySession.activity_id == activity_id
            ).order_by(ActivitySession.created_at.desc()).limit(10).all()
            
            return {
                "sessions": [
                    {
                        "status": session.status.value,
                        "time_spent": session.time_spent,
                        "date": session.created_at.isoformat()
                    }
                    for session in sessions
                ]
            }
        except Exception as e:
            logger.error(f"Error extracting progress data: {e}")
            return {}

    async def _extract_document_data(self, activity_id: str) -> List[Dict[str, Any]]:
        """Extract document data from database"""
        try:
            documents = self.db.query(DocumentModel).filter(
                DocumentModel.activity_id == activity_id,
                DocumentModel.is_processed == True
            ).all()
            
            return [
                {
                    "id": str(doc.id),
                    "name": doc.name,
                    "type": doc.document_type
                }
                for doc in documents
            ]
        except Exception as e:
            logger.error(f"Error extracting document data: {e}")
            return []

    async def _extract_reflection_data(self, state: Dict[str, Any]) -> str:
        """Extract reflection data from state"""
        return state.get("chat_context", "")

    async def _extract_project_data(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract project data from state"""
        return {}

    async def _extract_presentation_data(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract presentation data from state"""
        return {}

    async def evaluate(self, user_id: UUID, activity_id: UUID, session_id: Optional[UUID] = None, 
                      chat_context: str = "", triggered_by: str = "ui") -> Dict[str, Any]:
        """Main evaluation method"""
        
        # Create evaluation record
        evaluation = EvaluationResult(
            user_id=user_id,
            activity_id=activity_id,
            session_id=session_id,
            evaluation_type=EvaluationType.COMPREHENSIVE,
            status=EvaluationStatus.IN_PROGRESS,
            triggered_by=triggered_by
        )
        
        self.db.add(evaluation)
        self.db.commit()
        
        try:
            # Initialize state
            state = {
                "user_id": str(user_id),
                "activity_id": str(activity_id),
                "session_id": str(session_id) if session_id else None,
                "chat_context": chat_context,
                "evaluation_id": str(evaluation.id)
            }
            
            # Run evaluation workflow
            result = await self.workflow.ainvoke(state)
            
            # Store evaluation embeddings in pgvector for future similarity search
            final_report = result.get("report", {})
            if final_report:
                await self.pgvector_service.add_evaluation_embedding(
                    evaluation_id=str(evaluation.id),
                    user_id=str(user_id),
                    activity_id=str(activity_id),
                    content_type="evaluation_summary",
                    content_text=f"Evaluation: {final_report.get('overall_score', 0)}% score for {final_report.get('evaluation_type', 'unknown')} type",
                    metadata={
                        "evaluation_type": final_report.get("evaluation_type"),
                        "overall_score": final_report.get("overall_score"),
                        "triggered_by": triggered_by
                    }
                )
            
            # Update evaluation record with results
            evaluation.overall_score = final_report.get("overall_score")
            evaluation.status = EvaluationStatus.COMPLETED
            evaluation.completed_at = datetime.now()
            
            self.db.commit()
            
            logger.info(f"Evaluation completed successfully for user {user_id}")
            return final_report
            
        except Exception as e:
            evaluation.status = EvaluationStatus.FAILED
            self.db.commit()
            logger.error(f"Evaluation failed: {str(e)}")
            raise 

    async def analyze_academic_input(
        self, 
        content: str, 
        user_id: Optional[str] = None,
        activity_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Intelligent Evaluator Agent for dynamic academic input analysis
        
        This method analyzes academic input and returns classification with collection structure
        for modular embedding storage in pgvector.
        
        Args:
            content: The academic content to analyze
            user_id: Optional user identifier
            activity_id: Optional activity identifier
            metadata: Additional metadata about the content
            
        Returns:
            Dictionary with content_type, subject, student_id, collection, and evaluation_strategy
        """
        
        # Define content types and evaluation strategies
        content_types = [
            "lecture_notes", "quiz_response", "mock_test", "student_feedback", 
            "progress_log", "project_work", "code_submission", "reflection", 
            "discussion", "assignment", "presentation", "lab_report", "unknown"
        ]
        
        evaluation_strategies = [
            "rag_contextual_answering", "scoring", "summarization", 
            "sentiment_analysis", "code_review", "rubric_alignment", 
            "feedback_analysis", "comprehension_check", "peer_review", "unknown"
        ]
        
        try:
            # Step 1: Extract basic information
            extracted_info = self._extract_basic_info(content, user_id, activity_id, metadata)
            
            # Step 2: Use LLM for intelligent classification
            llm_analysis = await self._llm_classification(content, extracted_info, content_types, evaluation_strategies)
            
            # Step 3: Combine and validate results
            final_result = self._combine_analysis(extracted_info, llm_analysis, content_types, evaluation_strategies)
            
            # Step 4: Store in pgvector collection
            await self._store_in_collection(final_result, content, metadata)
            
            logger.info(f"Academic input analyzed: {final_result['content_type']} -> {final_result['collection']}")
            return final_result
            
        except Exception as e:
            logger.error(f"Error analyzing academic input: {e}")
            return self._get_fallback_result(user_id, activity_id)
    
    def _extract_basic_info(
        self, 
        content: str, 
        user_id: Optional[str] = None,
        activity_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Extract basic information using pattern matching"""
        
        # Extract student ID
        student_id = self._extract_student_id(content, user_id, activity_id, metadata)
        
        # Extract subject using pattern matching
        subject = self._extract_subject_pattern(content, metadata)
        
        # Extract content type hints
        content_type_hints = self._extract_content_type_hints(content, metadata)
        
        return {
            "student_id": student_id,
            "subject": subject,
            "content_type_hints": content_type_hints,
            "word_count": len(content.split()),
            "has_code": self._contains_code(content),
            "has_math": self._contains_math(content),
            "has_questions": self._contains_questions(content)
        }
    
    def _extract_student_id(
        self, 
        content: str, 
        user_id: Optional[str] = None,
        activity_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Extract or infer student ID"""
        
        # Priority order: metadata > user_id > activity_id > content extraction > general
        
        if metadata and metadata.get("student_id"):
            return str(metadata["student_id"])
        
        if user_id:
            return str(user_id)
        
        if activity_id:
            return f"activity_{activity_id}"
        
        # Try to extract from content
        patterns = [
            r"student[_\s]?id[:\s]*([a-zA-Z0-9_-]+)",
            r"user[_\s]?id[:\s]*([a-zA-Z0-9_-]+)",
            r"id[:\s]*([a-zA-Z0-9_-]{8,})",
            r"([a-zA-Z0-9_-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"  # Email
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return "general"
    
    def _extract_subject_pattern(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Extract subject using pattern matching"""
        
        # Check metadata first
        if metadata and metadata.get("subject"):
            return metadata["subject"].lower()
        
        # Check activity subject if available
        if metadata and metadata.get("activity_subject"):
            return metadata["activity_subject"].lower()
        
        # Subject patterns for common academic subjects
        subject_patterns = {
            "mathematics": ["math", "algebra", "calculus", "geometry", "statistics", "trigonometry"],
            "computer_science": ["programming", "coding", "algorithm", "data structure", "software", "computer"],
            "physics": ["physics", "mechanics", "thermodynamics", "electromagnetism", "quantum"],
            "chemistry": ["chemistry", "organic", "inorganic", "biochemistry", "molecular"],
            "biology": ["biology", "anatomy", "physiology", "genetics", "ecology"],
            "literature": ["literature", "poetry", "novel", "drama", "fiction"],
            "history": ["history", "historical", "ancient", "medieval", "modern"],
            "economics": ["economics", "microeconomics", "macroeconomics", "finance"],
            "psychology": ["psychology", "cognitive", "behavioral", "clinical"],
            "engineering": ["engineering", "mechanical", "electrical", "civil", "chemical"],
            "machine_learning": ["ml", "machine learning", "neural network", "deep learning"],
            "data_science": ["data science", "data analysis", "pandas", "numpy"],
            "web_development": ["html", "css", "javascript", "web", "frontend", "backend"],
            "database": ["sql", "database", "mysql", "postgresql", "mongodb"],
            "artificial_intelligence": ["ai", "artificial intelligence", "neural", "algorithm"]
        }
        
        # Pattern matching in content
        content_lower = content.lower()
        
        for subject, patterns in subject_patterns.items():
            for pattern in patterns:
                if pattern in content_lower:
                    return subject
        
        return "general"
    
    def _extract_content_type_hints(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> List[str]:
        """Extract hints about content type"""
        
        hints = []
        content_lower = content.lower()
        
        # Check metadata
        if metadata:
            if metadata.get("content_type"):
                hints.append(metadata["content_type"])
            if metadata.get("is_quiz"):
                hints.append("quiz_response")
            if metadata.get("is_assignment"):
                hints.append("assignment")
        
        # Pattern-based hints
        if any(word in content_lower for word in ["question", "answer", "quiz", "test", "exam"]):
            hints.append("quiz_response")
        
        if any(word in content_lower for word in ["reflection", "thought", "learned", "realized"]):
            hints.append("reflection")
        
        if any(word in content_lower for word in ["project", "assignment", "homework"]):
            hints.append("project_work")
        
        if any(word in content_lower for word in ["def ", "class ", "function", "import", "print"]):
            hints.append("code_submission")
        
        if any(word in content_lower for word in ["lecture", "notes", "summary"]):
            hints.append("lecture_notes")
        
        if any(word in content_lower for word in ["feedback", "comment", "suggestion"]):
            hints.append("student_feedback")
        
        if any(word in content_lower for word in ["progress", "update", "status"]):
            hints.append("progress_log")
        
        if any(word in content_lower for word in ["discussion", "debate", "argument"]):
            hints.append("discussion")
        
        return hints
    
    def _contains_code(self, content: str) -> bool:
        """Check if content contains code"""
        code_patterns = [
            r"def\s+\w+",
            r"class\s+\w+",
            r"import\s+\w+",
            r"function\s+\w+",
            r"console\.log",
            r"print\(",
            r"return\s+",
            r"if\s*\(",
            r"for\s+\w+\s+in",
            r"while\s*\("
        ]
        
        return any(re.search(pattern, content, re.IGNORECASE) for pattern in code_patterns)
    
    def _contains_math(self, content: str) -> bool:
        """Check if content contains mathematical expressions"""
        math_patterns = [
            r"\d+\s*[+\-*/]\s*\d+",
            r"x\s*=\s*\d+",
            r"y\s*=\s*\d+",
            r"sqrt\(",
            r"sin\(",
            r"cos\(",
            r"tan\(",
            r"\^",
            r"\\frac",
            r"\\sqrt"
        ]
        
        return any(re.search(pattern, content) for pattern in math_patterns)
    
    def _contains_questions(self, content: str) -> bool:
        """Check if content contains questions"""
        question_patterns = [
            r"\?$",
            r"what\s+is",
            r"how\s+do",
            r"why\s+does",
            r"when\s+will",
            r"where\s+is",
            r"which\s+one",
            r"question\s+\d+"
        ]
        
        return any(re.search(pattern, content, re.IGNORECASE) for pattern in question_patterns)
    
    async def _llm_classification(
        self, 
        content: str, 
        extracted_info: Dict[str, Any],
        content_types: List[str],
        evaluation_strategies: List[str]
    ) -> Dict[str, Any]:
        """Use LLM for intelligent classification"""
        
        prompt = ChatPromptTemplate.from_template("""
        You are an expert academic content classifier. Analyze the following content and classify it accurately.

        Content: {content}

        Extracted Information:
        - Student ID: {student_id}
        - Subject: {subject}
        - Content Type Hints: {content_type_hints}
        - Word Count: {word_count}
        - Contains Code: {has_code}
        - Contains Math: {has_math}
        - Contains Questions: {has_questions}

        Available Content Types: {content_types}
        Available Evaluation Strategies: {evaluation_strategies}

        Based on the content and extracted information, determine:

        1. The most accurate content_type from the available options
        2. The specific subject/topic (be more specific than the extracted subject if possible)
        3. The best evaluation_strategy for this content

        Respond with a JSON object containing:
        - content_type: The most appropriate content type
        - subject: The specific subject/topic
        - evaluation_strategy: The best evaluation strategy

        Consider the following:
        - Quiz responses should be evaluated with "scoring"
        - Code submissions should use "code_review"
        - Reflections should use "sentiment_analysis"
        - Project work might use "rubric_alignment"
        - Questions might use "rag_contextual_answering"
        """)
        
        try:
            response = await llm.ainvoke(
                prompt.format(
                    content=content[:1000],  # Limit content length
                    student_id=extracted_info["student_id"],
                    subject=extracted_info["subject"],
                    content_type_hints=extracted_info["content_type_hints"],
                    word_count=extracted_info["word_count"],
                    has_code=extracted_info["has_code"],
                    has_math=extracted_info["has_math"],
                    has_questions=extracted_info["has_questions"],
                    content_types=content_types,
                    evaluation_strategies=evaluation_strategies
                )
            )
            
            # Parse JSON response
            try:
                llm_result = json.loads(response.content)
                return {
                    "content_type": llm_result.get("content_type", "unknown"),
                    "subject": llm_result.get("subject", extracted_info["subject"]),
                    "evaluation_strategy": llm_result.get("evaluation_strategy", "unknown")
                }
            except json.JSONDecodeError:
                logger.warning("Failed to parse LLM response as JSON")
                return self._fallback_llm_classification(content, extracted_info)
                
        except Exception as e:
            logger.error(f"LLM classification failed: {e}")
            return self._fallback_llm_classification(content, extracted_info)
    
    def _fallback_llm_classification(
        self, 
        content: str, 
        extracted_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback classification when LLM fails"""
        
        content_type = "unknown"
        evaluation_strategy = "unknown"
        
        # Simple rule-based classification
        if extracted_info["has_code"]:
            content_type = "code_submission"
            evaluation_strategy = "code_review"
        elif extracted_info["has_questions"]:
            content_type = "quiz_response"
            evaluation_strategy = "scoring"
        elif "reflection" in extracted_info["content_type_hints"]:
            content_type = "reflection"
            evaluation_strategy = "sentiment_analysis"
        elif "project" in extracted_info["content_type_hints"]:
            content_type = "project_work"
            evaluation_strategy = "rubric_alignment"
        elif "lecture" in extracted_info["content_type_hints"]:
            content_type = "lecture_notes"
            evaluation_strategy = "summarization"
        
        return {
            "content_type": content_type,
            "subject": extracted_info["subject"],
            "evaluation_strategy": evaluation_strategy
        }
    
    def _combine_analysis(
        self, 
        extracted_info: Dict[str, Any], 
        llm_analysis: Dict[str, Any],
        content_types: List[str],
        evaluation_strategies: List[str]
    ) -> Dict[str, Any]:
        """Combine extracted info and LLM analysis"""
        
        # Use LLM results, fallback to extracted info
        content_type = llm_analysis.get("content_type", "unknown")
        subject = llm_analysis.get("subject", extracted_info["subject"])
        evaluation_strategy = llm_analysis.get("evaluation_strategy", "unknown")
        student_id = extracted_info["student_id"]
        
        # Validate content_type
        if content_type not in content_types:
            content_type = "unknown"
        
        # Validate evaluation_strategy
        if evaluation_strategy not in evaluation_strategies:
            evaluation_strategy = "unknown"
        
        # Construct collection name
        collection = f"collection/{content_type}/{subject}/{student_id}"
        
        return {
            "content_type": content_type,
            "subject": subject,
            "student_id": student_id,
            "collection": collection,
            "evaluation_strategy": evaluation_strategy
        }
    
    async def _store_in_collection(
        self, 
        result: Dict[str, Any], 
        content: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Store content in pgvector collection"""
        
        try:
            # Create collection metadata
            collection_metadata = {
                "content_type": result["content_type"],
                "subject": result["subject"],
                "student_id": result["student_id"],
                "collection": result["collection"],
                "evaluation_strategy": result["evaluation_strategy"],
                "created_at": datetime.now().isoformat(),
                "original_metadata": metadata or {}
            }
            
            # Store in pgvector (this would need to be implemented in PgVectorService)
            # For now, we'll just log the storage attempt
            logger.info(f"Would store in collection: {result['collection']}")
            logger.info(f"Content length: {len(content)} characters")
            logger.info(f"Metadata: {collection_metadata}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error storing in collection: {e}")
            return False
    
    def _get_fallback_result(
        self, 
        user_id: Optional[str] = None,
        activity_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get fallback result when analysis fails"""
        
        student_id = str(user_id) if user_id else "general"
        
        return {
            "content_type": "unknown",
            "subject": "general",
            "student_id": student_id,
            "collection": f"collection/unknown/general/{student_id}",
            "evaluation_strategy": "unknown"
        }
    
    async def batch_analyze(
        self, 
        contents: List[Tuple[str, Optional[str], Optional[str], Optional[Dict[str, Any]]]]
    ) -> List[Dict[str, Any]]:
        """Analyze multiple academic inputs in batch"""
        
        results = []
        
        for content, user_id, activity_id, metadata in contents:
            try:
                result = await self.analyze_academic_input(content, user_id, activity_id, metadata)
                results.append(result)
            except Exception as e:
                logger.error(f"Error in batch analysis: {e}")
                results.append(self._get_fallback_result(user_id, activity_id))
        
        return results
    
    def get_collection_stats(self, collection_prefix: str = "collection") -> Dict[str, Any]:
        """Get statistics for collections"""
        
        try:
            # This would query pgvector for collection statistics
            # For now, return mock data
            return {
                "total_collections": 0,
                "collections_by_type": {},
                "collections_by_subject": {},
                "storage_size": "0 MB"
            }
        except Exception as e:
            logger.error(f"Error getting pgvector stats: {e}")
            return {"error": str(e)} 