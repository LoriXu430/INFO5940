# 📌 INFO-5940: Assignment 1: Development of RAG App 🤖
# 📝 Made by Zhiqian Xu 🚀

# RAG Chatbot App (`rag_app.py`)

Hey there! This is my RAG (Retrieval Augmented Generation) chatbot for INFO-5940 Assignment 1. 
It allows user to upload documents (PDFs and text files) and chat about them.

## What This Thing Can Do

- Chat with PDFs and text files
- Handle multiple files at once
- Break down huge documents into bite-sized chunks
- Auto-picks the best AI model available on the system

## Environment for Running

User will need:
- Docker
- VS Code with Remote Containers

### How to Start Running

1. Clone this repo
2. Open it in users own VS Code
3. When it asks, hit "Reopen in Container"
4. Create a `.env` file with API key:
   `OPENAI_API_KEY=${OPENAI_API_KEY}`
   `OPENAI_BASE_URL=${OPENAI_BASE_URL}`
5. Run it in bash or terminal
`streamlit run rag_app.py`
6. Check out http://localhost:8501 in browser

## How to Use the Chatbot

First, upload some files:
- Look for the left sidebar upload button
- Drag PDFs or text files there
- User can add multiple files

Then just start chatting:
- Type questions in the box at the bottom
- Ask about the uploaded documents
- Or just chat about whatever!

## What's logics behind the Chatbot

### Document Handling
The app chops up documents into smaller pieces with some overlap (so it doesn't lose context between chunks). 
Text files are easy to handle, but PDFs needed some extra work with PyPDF2.

### The Logics
When user asks a question, it:
1. Looks through uploaded docs for relevant info
2. Combines everything together for the AI
3. Uses the best available model

### Changes I Made to the Previous Template
I started with the chat_with_pdf.py and then chat_with_rag template but made many improvements:
- Added multi-document support
- Made it automatically detect available models
- Added better error handling
- Improved the chunking to maintain context better
- Wrote comments in the rag_app.py to better explain the logic on codes

## Troubleshooting
- Double-check the API key and its format
- Check the terminal for error messages
- Try turning it off and on again if no idea what's happening