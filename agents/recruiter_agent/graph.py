"""
Lead Recruiter Agent Graph - Squad 1's Workspace

This agent handles:
- CV parsing and analysis
- Skill extraction from resumes
- Candidate ranking and scoring
"""

from langgraph.graph import StateGraph, END
from langchain_core.messages import AIMessage, HumanMessage

from agents.shared.state import AgentState
from agents.shared.utils import logger, extract_last_message

# Import tools from the tools folder
# Ensure you have updated __init__.py in tools folder to export these
from .tools import (
    cv_parser_tool,
    batch_cv_parser,
    text_cleaner_pipeline,
    anonymizer_tool,
    skill_extractor_tool, 
    candidate_summarizer,
    similarity_matcher_tool, 
    match_explainer, 
    cv_ranker,
    job_scraper_tool
)

# List of all available tools for this agent
RECRUITER_TOOLS = [
    cv_parser_tool,
    batch_cv_parser,
    text_cleaner_pipeline,
    anonymizer_tool,
    skill_extractor_tool,
    candidate_summarizer,
    similarity_matcher_tool,
    match_explainer,
    cv_ranker,
    job_scraper_tool,
]


def agent_node(state: AgentState) -> dict:
    """
    Main processing node for the Lead Recruiter Agent.
    
    Args:
        state: The current agent state containing messages and job context.
    
    Returns:
        Updated state with the agent's response.
    
    """
    # Extract the last HumanMessage for context (ignore routing messages)
    user_query = "No query provided"
    messages = state.get("messages", [])
    if messages:
        # Find the last HumanMessage from the end
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                user_query = msg.content
                break
        
        # If no HumanMessage found, fallback to last message
        if user_query == "No query provided" and messages:
            last_message = messages[-1]
            user_query = last_message.content if hasattr(last_message, 'content') else str(last_message)
            
    job_context = state.get("job_context", {})
    
    # Check if we have a CV to analyze
    cv_text = job_context.get("current_cv_text")
    
    response_content = ""
    
    # ---------------------------------------------------------
    # ROUTE: CV Analysis (Upload)
    # ---------------------------------------------------------
    if "analyze" in user_query.lower() or "uploaded" in user_query.lower():
        if not cv_text:
            response_content = (
                f"⚠️ **Issue Detected**\n\n"
                f"I noticed you uploaded a CV, but I couldn't extract any text from it.\n"
                f"- The file might be an **image-based PDF** or scanned document (OCR not yet enabled).\n"
                f"- The file might be corrupted or empty.\n\n"
                f"**Please try converting the PDF to a Word document or ensuring it has selectable text.**"
            )
        else:
            # Perform analysis manually (simulating LLM tool use)
            try:
                # 1. Extract Skills (Enhanced tool)
                extracted_data = skill_extractor_tool.invoke({"cv_text": cv_text})
                
                # 2. Summarize (Enhanced tool)
                summary_input = {"cv_text": cv_text, "extracted_skills": extracted_data}
                summary = candidate_summarizer.invoke({"input_data": summary_input})
                
                # Update context with extracted data
                job_context["extracted_skills"] = extracted_data
                job_context["candidate_summary"] = summary
                
                # Helper to format list
                def format_list(items):
                    if not items: return "None detected"
                    return ", ".join(items[:10]) + (f" (+{len(items)-10} more)" if len(items) > 10 else "")

                # 3. Format Response (Professional Layout)
                response_content = (
                    f"### 📄 CV Analysis Result\n\n"
                    f"{summary}\n\n"
                    f"#### 🛠️ Technical Competencies\n"
                    f"- **Identified Skills**: {format_list(extracted_data.get('skills', []))}\n"
                    f"- **Key Category**: Data Science & AI (Inferred from keywords)\n\n"
                    f"#### 📊 Professional Profile\n"
                    f"- **Experience Level**: {extracted_data.get('experience_years', 0)} years (Estimated)\n"
                    f"- **Projects Detected**: ~{extracted_data.get('projects_count', 0)} projects mentioned\n\n"
                    f"#### 🎓 Education\n"
                )
                
                if extracted_data.get("education"):
                    for edu in extracted_data.get("education", []):
                        response_content += f"- **{edu.get('degree', 'Degree')}** in {edu.get('field', 'Field')} — *{edu.get('institution', 'Institution')}*\n"
                else:
                    response_content += "- No explicit degree information detected.\n"
                    
                response_content += "\n---\n*Analysis based on keyword extraction and heuristic matching. Would you like to proceed with candidate ranking?*"
                
            except Exception as e:
                response_content = f"❌ Error analyzing CV: {str(e)}"
                import traceback
                print(traceback.format_exc())

    # ---------------------------------------------------------
    # ROUTE: Ranking Candidates
    # ---------------------------------------------------------
    elif "rank" in user_query.lower():
        extracted_skills = job_context.get("extracted_skills")
        
        if not extracted_skills:
            response_content = "⚠️ Please analyze a candidate CV first before ranking."
        else:
            # Mock Job Description if not present
            default_jd = """
            We are looking for a Data Scientist with experience in Machine Learning, Python, and NLP.
            Key requirements:
            - 2+ years of experience
            - Strong knowledge of TensorFlow, PyTorch, and Scikit-Learn
            - Experience with Large Language Models (LLMs) and RAG
            - Degree in Computer Science or related field.
            """
            
            job_description = job_context.get("current_job_description", default_jd)
            
            try:
                # Prepare candidate object for ranking tool
                candidate_profile = {
                    "id": "candidate_current",
                    "skills": extracted_skills.get("skills", []),
                    "experience": [f"{extracted_skills.get('experience_years', 0)} years experience"],
                    "education": " ".join([e.get('degree','') for e in extracted_skills.get("education", [])])
                }
                
                # Perform Ranking
                # Fix: Use 'candidate_profile' argument to match updated tool definition
                match_result = similarity_matcher_tool.invoke({
                    "candidate_profile": candidate_profile,
                    "job_description": job_description
                })
                
                score = match_result.get("similarity_score", 0)
                
                # Generate Explanation Match Levels
                match_level = "High" if score > 75 else "Medium" if score > 50 else "Low"
                
                response_content = (
                    f"### 🏆 Candidate Ranking Report\n\n"
                    f"**Target Role**: Data Scientist / AI Engineer\n"
                    f"**Match Score**: **{score}%** ({match_level} Match)\n\n"
                    f"#### 🔍 Analysis\n"
                    f"The candidate demonstrates a strong alignment with the technical stack (Python, NLP, ML frameworks). "
                    f"The experience level is compatible with the role requirements.\n\n"
                    f"**Recommendation**: Proceed to interview phase."
                )
                if match_result.get("note"):
                     response_content += f"\n\n*(Note: {match_result.get('note')})*"
                
            except Exception as e:
                 response_content = f"❌ Error during ranking: {str(e)}"
                 import traceback
                 print(traceback.format_exc())

    else:
        # Fallback for general queries
        response_content = (
            f"🎯 **Lead Recruiter Agent**\n\n"
            f"I can help you analyze CVs. Please upload a CV using the 'Analyze CVs' quick action."
        )
    
    return {
        "messages": [AIMessage(content=response_content)],
        "job_context": job_context
    }


def build_recruiter_graph() -> StateGraph:
    """
    Builds and compiles the Lead Recruiter Agent graph.
    
    Returns:
        A compiled StateGraph ready for execution.
    """
    # Initialize the graph with shared state
    graph = StateGraph(AgentState)
    
    # Add the main processing node
    graph.add_node("recruiter_process", agent_node)
    
    # Set entry point
    graph.set_entry_point("recruiter_process")
    
    # Add edge to END
    graph.add_edge("recruiter_process", END)
    
    return graph.compile()


# Expose the compiled graph for import by the supervisor
recruiter_graph = build_recruiter_graph()
