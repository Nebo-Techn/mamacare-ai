import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any
import time
import traceback

# Configure page
st.set_page_config(
    page_title="Afyamama AI - Maternal Health RAG",
    page_icon="🤱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin: 0.5rem 0;
    }
    .source-card {
        background: #e3f2fd;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #2196f3;
    }
    .error-card {
        background: #ffebee;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #f44336;
        color: #c62828;
    }
    .success-card {
        background: #e8f5e8;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #4caf50;
        color: #2e7d32;
    }
</style>
""", unsafe_allow_html=True)

# API Configuration
API_BASE_URL = "https://upgraded-bassoon-g4q9rjxrrjg43vgjq-8001.app.github.dev"

def make_api_request(endpoint: str, method: str = "GET", data: dict = None, files: dict = None) -> Dict[str, Any]:
    """Make API request with detailed debug logging"""
    url = f"{API_BASE_URL}{endpoint}"
    # st.text(f"Making {method} request to: {url}")
    # st.text(f"Data: {data}")
    # st.text(f"Files: {files}")

    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            if files:
                response = requests.post(url, files=files, data=data)
            else:
                response = requests.post(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        else:
            raise ValueError(f"Unsupported method: {method}")

        st.text(f"Response status code: {response.status_code}")
        response.raise_for_status()
        st.text(f"Response content: {response.text}")
        return response.json()
    
    except requests.exceptions.ConnectionError as e:
        st.error("connect to API server. Please ensure the backend is running on port 8000.")
        st.error(f"ConnectionError: {e}")
        st.text(traceback.format_exc())
        st.header(f"URL tried: {url}")
        return {"error": "Connection failed"}
    except requests.exceptions.HTTPError as e:
        st.error(f"API HTTPError: {e}")
        st.text(traceback.format_exc())
        return {"error": str(e)}
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        st.text(traceback.format_exc())
        return {"error": str(e)}

def check_api_health() -> bool:
    """Check if API is healthy"""
    result = make_api_request("/health")
    return result.get("status") == "healthy"

# Main header
st.markdown("""
<div class="main-header">
    <h1>🤱 Afyamama AI - Maternal Health RAG System</h1>
    <p>Enhanced RAG system for maternal health in Swahili using PostgreSQL</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("🔧 System Status")

    
    # Health check
    if check_api_health():
        st.success("API Connected")
    else:
        st.error("API Disconnected")
        st.stop()

# Main tabs
tab1, tab2, tab4, tab5 = st.tabs([
    "💬 Ask Questions", 
    "📄 Document Management",  
    "🔄 Data Migration", 
    "⚙️ System Admin"
])

# Tab 1: Ask Questions
with tab1:
    st.header("💬 Ask Questions About Maternal Health")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        query = st.text_area(
            "Ask your question in Swahili:",
            placeholder="Mfano: Dalili za mimba changa ni zipi?",
            height=100
        )
        
        # Query parameters
        with st.expander("⚙️ Advanced Options"):
            k = st.slider("Number of chunks to retrieve", 1, 20, 10)
            similarity_threshold = st.slider("Similarity threshold", 0.0, 1.0, 0.7)
            include_sources = st.checkbox("Include sources", value=True)
    
    with col2:
        st.markdown("### 💡 Tips")
        st.markdown("""
        - Ask questions in Swahili
        - Be specific about symptoms or concerns
        - Questions about pregnancy, nutrition, and maternal health work best
        """)
    
    if st.button("🔍 Ask Question", type="primary"):
        if query.strip():
            with st.spinner("Processing your question..."):
                result = make_api_request("/ask", "POST", {
                    "query": query,
                    "k": k,
                    "similarity_threshold": similarity_threshold,
                    "include_sources": include_sources
                })
            
            if "error" not in result:
                st.markdown("### 💬 Answer")
                st.markdown(f"**{result['answer']}**")
                
                if result.get("sources"):
                    st.markdown("### 📚 Sources")
                    for i, source in enumerate(result["sources"][:5], 1):
                        st.markdown(f"""
                        <div class="source-card">
                            <strong>{i}. {source.get('title', 'Unknown')}</strong><br>
                            <small>Type: {source.get('type', 'Unknown')} | Similarity: {source.get('similarity', 0):.2f}</small>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Feedback section
                st.markdown("### 📝 Feedback")
                col1, col2 = st.columns(2)
                
                with col1:
                    feedback = st.text_area("Your feedback (optional):", height=80)
                
                with col2:
                    rating = st.selectbox("Rate this answer:", [None, 1, 2, 3, 4, 5])
                
                if st.button("Submit Feedback") and result.get("interaction_id"):
                    feedback_result = make_api_request("/feedback", "POST", {
                        "interaction_id": result["interaction_id"],
                        "feedback": feedback if backend.feedback.strip() else None,
                        "rating": rating
                    })
                    
                    if "error" not in feedback_result:
                        st.success("Feedback submitted successfully!")
                    else:
                        st.error("Failed to submit feedback")
            else:
                st.error(f"Error: {result['error']}")
        else:
            st.warning("Please enter a question")

# Tab 2: Document Management
with tab2:
    st.header("📄 Document Management")
    
    # Document upload section
    st.subheader("📤 Upload Documents")
    
    upload_type = st.radio("Select upload type:", ["PDF", "URL", "YouTube", "Facebook"])
    
    if upload_type == "PDF":
        uploaded_files = st.file_uploader("Upload PDF files", type=["pdf"], accept_multiple_files=True)
        if uploaded_files and st.button("Upload PDFs"):
            for file in uploaded_files:
                with st.spinner(f"Processing {file.name}..."):
                    files = {"file": (file.name, file, "application/pdf")}
                    result = make_api_request("/upload_pdf", "POST", files=files)
                    
                    if "error" not in result:
                        st.success(f"{file.name}: {result['chunks_created']} chunks created")
                    else:
                        st.error(f"{file.name}: {result['error']}")
    
    elif upload_type == "URL":
        url = st.text_input("Enter URL:")
        title = st.text_input("Title (optional):")
        if st.button("Upload URL") and url:
            with st.spinner("Processing URL..."):
                result = make_api_request("/upload_url", "POST", {"url": url, "title": title})
                
                if "error" not in result:
                    st.success(f"{result['title']}: {result['chunks_created']} chunks created")
                else:
                    st.error(f"{result['error']}")
    
    elif upload_type == "YouTube":
        youtube_url = st.text_input("Enter YouTube URL:")
        youtube_title = st.text_input("Title (optional):")
        if st.button("Upload YouTube Video") and youtube_url:
            with st.spinner("Processing YouTube video..."):
                result = make_api_request("/upload_youtube", "POST", {"url": youtube_url, "title": youtube_title})
                
                if "error" not in result:
                    st.success(f"{result['title']}: {result['chunks_created']} chunks created")
                else:
                    st.error(f"{result['error']}")
    
    elif upload_type == "Facebook":
        facebook_url = st.text_input("Enter Facebook post URL:")
        facebook_title = st.text_input("Title (optional):")
        if st.button("Upload Facebook Post") and facebook_url:
            with st.spinner("Processing Facebook post..."):
                result = make_api_request("/upload_facebook", "POST", {"url": facebook_url, "title": facebook_title})
                
                if "error" not in result:
                    st.success(f"{result['title']}: {result['chunks_created']} chunks created")
                else:
                    st.error(f"{result['error']}")
    
    # Document list section
    st.subheader("📋 Document List")
    
    if st.button("🔄 Refresh Documents"):
        documents = make_api_request("/documents")
        
        if "error" not in documents and documents.get("documents"):
            df = pd.DataFrame(documents["documents"])
            df['created_at'] = pd.to_datetime(df['created_at'])
            
            st.dataframe(
                df[['title', 'source_type', 'chunk_count', 'created_at']],
                use_container_width=True
            )
            
            # Document details
            if st.selectbox("View document details:", [""] + df['title'].tolist()):
                selected_doc = df[df['title'] == st.session_state.get('selectbox', '')].iloc[0]
                doc_details = make_api_request(f"/documents/{selected_doc['id']}")
                
                if "error" not in doc_details:
                    st.markdown(f"**Title:** {doc_details['title']}")
                    st.markdown(f"**Source:** {doc_details['source_url']}")
                    st.markdown(f"**Type:** {doc_details['source_type']}")
                    st.markdown(f"**Chunks:** {len(doc_details['chunks'])}")
                    
                    if st.button("🗑️ Delete Document"):
                        delete_result = make_api_request(f"/documents/{selected_doc['id']}", "DELETE")
                        if "error" not in delete_result:
                            st.success("✅ Document deleted successfully")
                            st.rerun()
                        else:
                            st.error(f"❌ {delete_result['error']}")
        else:
            st.info("No documents found")

# Tab 4: Data Migration
with tab4:
    st.header("🔄 Data Migration")
    st.info("Migrate existing data to the new PostgreSQL-based system")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Migrate Existing Chunks & Q&A"):
            with st.spinner("Migrating existing data..."):
                result = make_api_request("/migrate/existing-data", "POST")
                
                if "error" not in result:
                    st.success("Migration completed successfully!")
                    st.json(result.get("results"))
                else:
                    st.error(f"Migration failed: {result['error']}")
    
    with col2:
        if st.button("📄 Migrate Scraped Content"):
            with st.spinner("Migrating scraped content..."):
                result = make_api_request("/migrate/scraped-content", "POST")
                
                if "error" not in result:
                    st.success("Scraped content migration completed!")
                    st.json(result["results"])
                else:
                    st.error(f"Migration failed: {result['error']}")

# Tab 5: System Admin
with tab5:
    st.header("⚙️ System Administration")
    
    # Health check
    st.subheader("🔍 System Health")
    health = make_api_request("/health")
    
    if "error" not in health:
        st.json(health)
    else:
        st.error(f"Health check failed: {health['error']}")
    
    # Database operations
    st.subheader("🗄️ Database Operations")
    
    if st.button("🔄 Reindex All Documents"):
        st.warning("This will reindex all documents. This may take a while.")
        # Implementation would go here
    
    # System logs
    st.subheader("📋 System Information")
    st.info("""
    **System Version:** 2.0.0
    **Database:** PostgreSQL with pgvector
    **Embedding Model:** sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
    **LLM Model:** LoRA fine-tuned maternal health model
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666;">
    <p>🤱 Afyamama AI - Maternal Health RAG System v2.0 | Powered by PostgreSQL & pgvector</p>
</div>
""", unsafe_allow_html=True)