"""
Intelligent HR Recruitment Platform - Main Application

A Multi-Agent System (MAS) powered by LangGraph for intelligent recruitment.
Features a hierarchical supervisor pattern routing between specialized agents.
"""

import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage

from agents.supervisor import supervisor_graph
from agents.recruiter_agent.tools.parsers import cv_parser_tool


# Page configuration
st.set_page_config(
    page_title="HR Recruitment Platform",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .main-header {
        text-align: center;
        padding: 1rem 0;
        border-bottom: 2px solid #e0e0e0;
        margin-bottom: 2rem;
    }
    .agent-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 0.5rem;
        color: white;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "job_context" not in st.session_state:
        st.session_state.job_context = {}


def render_sidebar():
    """Render the sidebar with agent information and controls."""
    with st.sidebar:
        st.header("🤖 Agent System")
        
        st.markdown("### Available Agents")
        
        # Lead Recruiter Card
        with st.expander("🎯 Lead Recruiter", expanded=True):
            st.markdown("""
            **Capabilities:**
            - CV/Resume Parsing
            - Skill Extraction
            - Candidate Ranking
            - Application Screening
            
            *Trigger words: analyze, rank, parse, CV, candidate, skill*
            """)
        
        # Hiring Manager Card
        with st.expander("📝 Hiring Manager", expanded=True):
            st.markdown("""
            **Capabilities:**
            - Job Offer Generation
            - Template Retrieval (RAG)
            - Email Drafting
            - Interview Communications
            
            *Trigger words: offer, template, email, draft, write*
            """)
        
        st.markdown("---")
        
        # Job Context Display
        st.markdown("### 📋 Current Job Context")
        if st.session_state.job_context:
            st.json(st.session_state.job_context)
        else:
            st.info("No context yet. Start a conversation!")
        
        st.markdown("---")
        
        # Controls
        if st.button("🗑️ Clear Conversation", use_container_width=True):
            st.session_state.messages = []
            st.session_state.job_context = {}
            if "pending_action" in st.session_state:
                del st.session_state.pending_action
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 📊 System Status")
        st.success("✅ Supervisor: Online")
        st.success("✅ Lead Recruiter: Ready")
        st.success("✅ Hiring Manager: Ready")


def process_graph_request(user_message):
    """Process a request through the supervisor graph (helper function)."""
    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            try:
                # Prepare input state
                input_state = {
                    "messages": [user_message],
                    "next": "",
                    "job_context": st.session_state.job_context
                }
                
                # Stream/invoke the graph
                result = supervisor_graph.invoke(input_state)
                
                # Extract and display responses
                response_messages = result.get("messages", [])
                
                for msg in response_messages:
                    if isinstance(msg, AIMessage):
                        st.markdown(msg.content)
                        st.session_state.messages.append(msg)
                
                # Update job context
                if result.get("job_context"):
                    st.session_state.job_context.update(result["job_context"])
            
            except Exception as e:
                error_msg = f"❌ Error processing request: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append(AIMessage(content=error_msg))


def render_chat_interface():
    """Render the main chat interface."""
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🎯 Intelligent HR Recruitment Platform</h1>
        <p>Multi-Agent System powered by LangGraph</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Display chat messages
    for message in st.session_state.messages:
        if isinstance(message, HumanMessage):
            with st.chat_message("user"):
                st.markdown(message.content)
        elif isinstance(message, AIMessage):
            with st.chat_message("assistant"):
                st.markdown(message.content)
    
    # Chat input
    if user_input := st.chat_input("Ask about candidates, job offers, or recruitment tasks..."):
        # Add user message to state
        user_message = HumanMessage(content=user_input)
        st.session_state.messages.append(user_message)
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # Process through supervisor graph
        process_graph_request(user_message)


def render_quick_actions():
    """Render quick action buttons for common tasks."""
    st.markdown("### ⚡ Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📄 Analyze CVs", use_container_width=True):
            st.session_state.pending_action = "analyze_cv"
            st.rerun()
    
    with col2:
        if st.button("🏆 Rank Candidates", use_container_width=True):
            st.session_state.pending_action = "Rank the candidates based on their qualifications"
            st.rerun()
    
    with col3:
        if st.button("📝 Draft Job Offer", use_container_width=True):
            st.session_state.pending_action = "Write a job offer letter for the selected candidate"
            st.rerun()
    
    with col4:
        if st.button("✉️ Email Template", use_container_width=True):
            st.session_state.pending_action = "Get an email template for interview invitation"
            st.rerun()


def handle_cv_upload():
    """Handle CV upload and parsing."""
    st.markdown("### 📄 Upload CV for Analysis")
    uploaded_file = st.file_uploader("Choose a PDF or DOCX file", type=['pdf', 'docx'])
    
    if uploaded_file is not None:
        if st.button("Process CV", key="process_cv_btn"):
            with st.spinner("Parsing CV..."):
                try:
                    # Use the parser tool
                    # Pass the uploaded_file directly
                    result = cv_parser_tool.invoke({"file_obj": uploaded_file})
                    
                    if result.get("error"):
                        st.error(f"Error parsing CV: {result['error']}")
                    else:
                        st.success("CV parsed successfully!")
                        
                        # Store in job context
                        st.session_state.job_context["current_cv_text"] = result["text"]
                        st.session_state.job_context["current_cv_meta"] = {
                            "filename": result["filename"],
                            "pages": result["pages"]
                        }
                        
                        # Add a system message about the upload
                        msg_content = f"I have uploaded a CV for analysis: {result['filename']}."
                        if result["ocr_required"]:
                             msg_content += "\n(Note: OCR might be required for better accuracy)"
                             
                        user_msg = HumanMessage(content=msg_content)
                        st.session_state.messages.append(user_msg)
                        
                        # Clear pending action to return to main view
                        if "pending_action" in st.session_state:
                            del st.session_state.pending_action
                        
                        # Trigger analysis automatically by invoking supervisor
                        process_graph_request(user_msg)
                                
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
                    # print full traceback for debugging
                    import traceback
                    st.text(traceback.format_exc())

    if st.button("Cancel Upload"):
        if "pending_action" in st.session_state:
            del st.session_state.pending_action
        st.rerun()


def main():
    """Main application entry point."""
    # Initialize session state
    initialize_session_state()
    
    # Check for pending actions from quick action buttons
    # We handle this BEFORE rendering chat interface so the new message is visible
    # But ideally we want to trigger processing too.
    
    if "pending_action" in st.session_state:
        action = st.session_state.pending_action
        
        if action == "analyze_cv":
            # Render sidebar but replace main area with upload interface
            render_sidebar()
            handle_cv_upload()
            return # Stop execution here for upload view
            
        elif isinstance(action, str):
            # For other actions, just treat them as messages
            del st.session_state.pending_action
            user_message = HumanMessage(content=action)
            st.session_state.messages.append(user_message)
            # We DONT rerun immediately. We let the script flow down to render_chat_interface
            # where the message will be displayed.
            # AND we need to make sure the graph is invoked.
            
            # Since render_chat_interface logic is stuck inside "if user_input", 
            # we need to trigger it manually here.
            
            # Render sidebar
            render_sidebar()
            
            # Render chat interface (to show history + new message)
            # But render_chat_interface only shows messages, and waits for input.
            # We need to manually invoke processing for this action.
            
            # Header
            st.markdown("""
            <div class="main-header">
                <h1>🎯 Intelligent HR Recruitment Platform</h1>
                <p>Multi-Agent System powered by LangGraph</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Display chat messages (including the one we just added)
            # Note: The logic in render_chat_interface loops state.messages,
            # so we just need to replicate the input box and footer appearance
            
            # Actually, cleaner approach:
            # 1. We process the message
            # 2. We set a flag or just execute normal flow
            
            # Reusing render_chat_interface() but without waiting for input first?
            # No, render_chat_interface does the loop. 
            # We want to insert the processing.

            # We don't import HumanMessage here as it is already imported in global scope
            
            # Render all previous messages including the new one
            for message in st.session_state.messages:
                if isinstance(message, HumanMessage):
                    with st.chat_message("user"):
                        st.markdown(message.content)
                elif isinstance(message, AIMessage):
                    with st.chat_message("assistant"):
                        st.markdown(message.content)
            
            # NOW Trigger processing which will add the AI response
            process_graph_request(user_message)
            
            # Show input for future messages
            user_input = st.chat_input("Ask about candidates, job offers, or recruitment tasks...")
            if user_input:
                # This block handles input if the user types quickly after action, 
                # but standard flow handles it on next rerun. 
                # We can just ignore for this frame.
                pass
            
            # Render quick actions
            with st.container():
                st.markdown("---")
                render_quick_actions()
                
            # Footer
            st.markdown("---")
            st.markdown(
                "<div style='text-align: center; color: #888;'>"
                "Built with ❤️ using LangGraph & Streamlit | "
                "Hierarchical Supervisor Pattern"
                "</div>",
                unsafe_allow_html=True
            )
            return # End execution here to avoid double rendering


    # Normal Flow (No pending action)
    render_sidebar()
    render_chat_interface()
    
    with st.container():
        st.markdown("---")
        render_quick_actions()
    
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #888;'>"
        "Built with ❤️ using LangGraph & Streamlit | "
        "Hierarchical Supervisor Pattern"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()