import streamlit as st
from openai import OpenAI
from os import environ
import PyPDF2
import os
import uuid
from io import BytesIO
from dotenv import load_dotenv

# load env vars
load_dotenv()

st.title("🤖 RAG Chatbot 📝")
st.caption("Powered by INFO-5940: Zhiqian Xu")

# create some memory for chatbot
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Hello! How can I help you today?"}]

# somewhere to keep all those uploaded files
if "document_store" not in st.session_state:
    # Store documents in memory
    st.session_state["document_store"] = {}

# Keep track of what AI models can use
if "available_models" not in st.session_state:
    st.session_state["available_models"] = []

# Get API Key from the environemnt
api_key = os.environ.get('OPENAI_API_KEY')
base_url = os.environ.get('OPENAI_BASE_URL')

if not api_key:
    st.error("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
    st.stop()

client = OpenAI(
    api_key=api_key,
    base_url=base_url if base_url else None
)

# Check which available models can use
try:
    with st.sidebar.expander("Available Models"):
        if not st.session_state["available_models"]:
            models = client.models.list()
            for model in models.data:
                st.session_state["available_models"].append(model.id)
        
        for model in st.session_state["available_models"]:
            st.write(f"- {model}")
        
        if st.session_state["available_models"]:
            default_model = st.session_state["available_models"][0]
            st.success(f"Using default model: {default_model}")
        else:
            default_model = "text-davinci-003" 
            st.warning(f"No models found, using fallback: {default_model}")
except Exception as e:
    st.sidebar.error(f"Error listing models: {str(e)}")
    default_model = "text-davinci-003"

# chops up long text into bite-sized pieces
def chunk_text(text, chunk_size=2000, overlap=200):
    """Break text into chunks with overlap."""
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunks.append(text[i:i + chunk_size])
    return chunks

# handle different file types
def process_text_file(uploaded_file):
    """Extract and chunk text from a .txt file."""
    text = uploaded_file.read().decode("utf-8")
    return chunk_text(text)

def process_pdf_file(uploaded_file):
    """Extract and chunk text from a .pdf file."""
    pdf_reader = PyPDF2.PdfReader(BytesIO(uploaded_file.read()))
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() or ""
    return chunk_text(text)

# Set up the sidebar where users can upload files
with st.sidebar:
    st.header("Document Upload")
    uploaded_files = st.file_uploader("Upload documents", 
                                     type=["txt", "pdf"], 
                                     accept_multiple_files=True)
    
    # Process uploaded files
    if uploaded_files:
        for uploaded_file in uploaded_files:
            # Check if file is already processed
            if uploaded_file.name not in st.session_state["document_store"]:
                file_type = uploaded_file.name.split(".")[-1].lower()
                
                with st.spinner(f"Processing {uploaded_file.name}..."):
                    if file_type == "txt":
                        chunks = process_text_file(uploaded_file)
                    elif file_type == "pdf":
                        chunks = process_pdf_file(uploaded_file)
                    else:
                        st.warning(f"Unsupported file type: {file_type}")
                        continue
                    
                    # Save the processed file chunks for later
                    doc_id = str(uuid.uuid4())
                    st.session_state["document_store"][uploaded_file.name] = {
                        "id": doc_id,
                        "type": file_type,
                        "chunks": chunks
                    }
                    st.success(f"Processed {uploaded_file.name}")

    if st.session_state["document_store"]:
        st.header("Uploaded Documents")
        for doc_name in st.session_state["document_store"]:
            st.write(f"- {doc_name}")

# Chat interface
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# This is the input box where users type their questions
prompt = st.chat_input("Ask a question about documents or universities...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # If documents have been uploaded, add their content to context
    has_uploaded_docs = len(st.session_state["document_store"]) > 0
    
    if has_uploaded_docs:
        all_documents_text = ""
        for doc_name, doc_data in st.session_state["document_store"].items():
            all_documents_text += f"\n\n--- Document: {doc_name} ---\n"
            all_documents_text += "\n".join(doc_data["chunks"])
        
        # Make sure don't overflow the context window
        if len(all_documents_text) > 100000:  # Arbitrary limit for context
            all_documents_text = all_documents_text[:100000] + "...(truncated)"
    
    try:
        # use the model to parse if the prompt is about a question about cornell, harvard or duke.
        model_to_use = "openai.gpt-4o-mini" if "openai.gpt-4o-mini" in st.session_state["available_models"] else default_model
        university_response = client.chat.completions.create(
            model=model_to_use, 
            messages=[
                {
                    "role": "system",
                    "content": """Your job is to guess which knowledge base I need to load based on the user 
                    prompt. The available knowledge bases are:
                    harvard.txt, cornell.txt, duke.txt if these are not related to the prompt please 
                    output none.txt.
                    I want you output to only be the name of the file. and nothing else.""",
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ])
        university_file = university_response.choices[0].message.content
        print(f"Detected university file: {university_file}")
    except Exception as e:
        university_file = "none.txt"
        print(f"Error detecting university: {str(e)}")
    
    # Process the response based on context
    try:
        if university_file in ["harvard.txt", "cornell.txt", "duke.txt"]:
            knowledge_base_file_path = "/workspace/data/knowledge_base"
            try:
                with open(f"{knowledge_base_file_path}/{university_file}", "r") as file:
                    content = file.read()
                print(f"Loaded university content: {len(content)} characters")
                
                # If we also have uploaded documents, combine their content
                if has_uploaded_docs:
                    content += f"\n\nUploaded Document Content:\n{all_documents_text}"
                
                with st.chat_message("assistant"):
                    model_to_use = "openai.gpt-4o" if "openai.gpt-4o" in st.session_state["available_models"] else default_model
                    stream = client.chat.completions.create(
                        model=model_to_use,
                        messages=[
                            {"role": "system", "content": f"Here's the content of the file:\n\n{content}"},
                            *st.session_state.messages
                        ],
                        stream=True
                    )
                    response = st.write_stream(stream)
            except FileNotFoundError:
                # Fall back to using uploaded documents if the file doesn't exist
                if has_uploaded_docs:
                    with st.chat_message("assistant"):
                        model_to_use = "openai.gpt-4o" if "openai.gpt-4o" in st.session_state["available_models"] else default_model
                        stream = client.chat.completions.create(
                            model=model_to_use,
                            messages=[
                                {"role": "system", "content": f"You are a helpful assistant that answers questions based on the provided documents. Only use information from the documents to answer. If the answer cannot be found in the documents, say so.\n\nDocument content:\n{all_documents_text}"},
                                {"role": "user", "content": prompt}
                            ],
                            stream=True
                        )
                        response = st.write_stream(stream)
                else:
                    # No documents or knowledge base, use general chat
                    with st.chat_message("assistant"):
                        model_to_use = "openai.gpt-4o" if "openai.gpt-4o" in st.session_state["available_models"] else default_model
                        stream = client.chat.completions.create(
                            model=model_to_use, 
                            messages=st.session_state.messages,
                            stream=True
                        )
                        response = st.write_stream(stream)
        
        elif has_uploaded_docs:
            with st.chat_message("assistant"):
                model_to_use = "openai.gpt-4o" if "openai.gpt-4o" in st.session_state["available_models"] else default_model
                stream = client.chat.completions.create(
                    model=model_to_use,
                    messages=[
                        {"role": "system", "content": f"You are a helpful assistant that answers questions based on the provided documents. Only use information from the documents to answer. If the answer cannot be found in the documents, say so.\n\nDocument content:\n{all_documents_text}"},
                        {"role": "user", "content": prompt}
                    ],
                    stream=True
                )
                response = st.write_stream(stream)
        
        else:
            with st.chat_message("assistant"):
                model_to_use = "openai.gpt-4o" if "openai.gpt-4o" in st.session_state["available_models"] else default_model
                stream = client.chat.completions.create(
                    model=model_to_use, 
                    messages=st.session_state.messages,
                    stream=True
                )
                response = st.write_stream(stream)
        
        # Keep a record of what the assistant said
        st.session_state.messages.append({"role": "assistant", "content": response})
    
    except Exception as e:
        error_msg = f"An error occurred: {str(e)}"
        st.error(error_msg)
        st.session_state.messages.append({"role": "assistant", "content": error_msg})