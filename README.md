# AI Customer Support System

This is a project I built to create a simple AI-based customer support system for an e-commerce application.

The main idea was to allow customers to ask questions about things like delivery, refunds, payments, cancellations and account issues. The system uses RAG to find relevant information from a knowledge base before generating an answer, and stores conversations and support tickets in MySQL.

I also built a Streamlit interface to interact with the system.

## What it does

- Answers customer support questions
- Searches the knowledge base using RAG
- Uses FAISS for finding relevant information
- Generates answers using Google Gemini
- Classifies questions into different support categories
- Stores conversations in MySQL
- Allows users to create support tickets
- Provides a Streamlit interface

## Tech Stack

- Python
- FastAPI
- MySQL
- SQLAlchemy
- LangChain
- FAISS
- Google Gemini
- Streamlit
- Pytest

## How it works

```text
Customer Question
        |
        v
    FastAPI
        |
        v
   RAG / FAISS
        |
        v
Relevant Information
        |
        v
   Gemini
        |
        v
     Answer
        |
        v
Store Conversation
        |
        v
     MySQL
```