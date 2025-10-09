import streamlit as st
import requests

st.title("Maternal Health RAG Demo")

st.header("Upload Documents")
option = st.radio("Select upload type:", ["PDF(s)", "URL(s)"])

if option == "PDF(s)":
    pdf_files = st.file_uploader("Upload one or more PDFs", type=["pdf"], accept_multiple_files=True)
    if pdf_files and st.button("Index PDF(s)"):
        if len(pdf_files) == 1:
            files = {"file": pdf_files[0]}
            res = requests.post("http://localhost:8000/upload_pdf", files=files)
        else:
            files = [("files", (f.name, f, "application/pdf")) for f in pdf_files]
            res = requests.post("http://localhost:8000/upload_pdfs", files=files)
        st.success(res.json().get("status", "Indexed"))
else:
    url_text = st.text_area("Enter one URL per line")
    if st.button("Index URL(s)") and url_text.strip():
        urls = [u.strip() for u in url_text.splitlines() if u.strip()]
        if len(urls) == 1:
            res = requests.post("http://localhost:8000/upload_url", data={"url": urls[0]})
        else:
            res = requests.post("http://localhost:8000/upload_urls", json={"urls": urls})
        st.success(res.json().get("status", "Indexed"))

st.header("Ask a Question")
query = st.text_input("Your question")
if st.button("Ask") and query:
    res = requests.post("http://localhost:8000/ask", json={"query": query})
    answer = res.json().get("answer", "")
    sources = res.json().get("sources", [])
    st.markdown(f"**Answer:** {answer}")
    if sources:
        st.markdown("**Sources:**")
        for src in sources:
            st.code(src)
