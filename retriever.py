import os
import streamlit as st
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers.ensemble import EnsembleRetriever
from langchain_core.documents import Document
from ingest_products import PRODUCTS

def get_ensemble_retriever(api_key: str):
    if not os.path.exists("./chroma_db"):
        return None
        
    embeddings = OpenAIEmbeddings(api_key=api_key)
    vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
    semantic_retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    
    documents = []
    for p in PRODUCTS:
        text = f"Name: {p['name']}\nDescription: {p['description']}\nCategory: {p['category']}\nPrice: ${p['price']}"
        documents.append(Document(page_content=text, metadata={"id": p['id'], "category": p['category'], "price": p['price'], "image": p['image']}))
    
    bm25_retriever = BM25Retriever.from_documents(documents)
    bm25_retriever.k = 3
    
    return EnsembleRetriever(
        retrievers=[bm25_retriever, semantic_retriever], weights=[0.5, 0.5]
    )
