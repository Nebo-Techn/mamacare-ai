import streamlit as st
import requests

st.title("Maternal Health RAG Demo")

st.header("Upload Document")
option = st.radio("Select upload type:", ["PDF", "URL"])

if option == "PDF":
    pdf_file = st.file_uploader("Upload PDF", type=["pdf"])
    if pdf_file:
        files = {"file": pdf_file}
        res = requests.post("http://localhost:8000/upload_pdf", files=files)
        st.success(res.json()["status"])
else:
    url = st.text_input("Enter URL")
    if st.button("Upload URL") and url:
        res = requests.post("http://localhost:8000/upload_url", data={"url": url})
        st.success(res.json()["status"])

st.header("Ask a Question")
query = st.text_input("Your question")
if st.button("Ask") and query:
    res = requests.post("http://localhost:8000/ask", json={"query": query})
    answer = res.json().get("answer", "")
    sources = res.json().get("sources", [])
    st.markdown(f"**Answer:** {answer}")
    st.markdown("**Sources:**")
    for src in sources:
        st.code(src)
