# Architecture: E-commerce Clothes Chatbot (Advanced)

This document tracks the backend (BE) stages, libraries, and advanced optimizations for our production-grade retail chatbot.

---

## 🛠 Progress Tracker
- [x] **Stage 1**: Intent Routing (Agentic)
- [x] **Stage 2**: Semantic Search (ChromaDB)
- [x] **Stage 2.1**: Hybrid Search (BM25 + Semantic)
- [ ] **Stage 2.2**: Re-ranking (Cohere/BGE)
- [x] **Stage 3**: Recommendation UI (Basic)
- [x] **Stage 3.1**: Visual Product Cards
- [ ] **Stage 4**: Knowledge Inquiry (RAG)
- [x] **Stage 5.1**: Style Recommendations Tool
- [x] **Stage 6**: Checkout Integration
- [ ] **LLMOps**: Evaluation & Guardrails
- [ ] **LLMOps**: Evaluation & Guardrails
- [ ] **LLMOps**: Semantic Caching

---

## Stage 1: Intent Routing & Contextual Awareness
**Context**: User initiates interaction.
**Status**: ✅ Implemented

| Component | Library / Module | Advanced Technique | Status |
| :--- | :--- | :--- | :--- |
| **Agent Core** | `LangGraph` | **create_react_agent** | ✅ |
| **User Profile** | `Pydantic` | **Context Injection** | ⏳ |
| **Session Memory** | `Redis` | **TTL Management** | ⏳ (using RAM) |

---

## Stage 2: Product Discovery (Advanced RAG)
**Context**: User searches for items.
**Status**: 🏗 In Progress

| Component | Library / Module | Advanced Technique | Status |
| :--- | :--- | :--- | :--- |
| **Retriever** | `EnsembleRetriever` | **Hybrid Search** | ✅ |
| **Vector Store** | `ChromaDB` | **Semantic Search** | ✅ |
| **Refinement** | `CohereRerank` | **Re-ranking** | ⏳ |

---

## Stage 3: Recommendation & UI Rendering
**Context**: Presenting items to the user.
**Status**: 🏗 In Progress

| Component | Library / Module | Advanced Technique | Status |
| :--- | :--- | :--- | :--- |
| **Output Format** | `LangChain JSON` | **Structured Output** | ⏳ |
| **Streaming** | `astream_events` | **Granular Streaming** | ⏳ |
| **Visuals** | `Streamlit` | **Product Cards** | ⏳ |

---

## Stage 5: Stateful Agent & Transactions
**Context**: Adding to cart and finalizing purchase.
**Status**: ✅ Implemented (Base)

| Component | Library / Module | Advanced Technique | Status |
| :--- | :--- | :--- | :--- |
| **Cart Tools** | `Custom Python` | **add_to_cart** | ✅ |
| **Cart Tools** | `Custom Python` | **remove_from_cart** | ✅ |
| **Stylist Tools** | `Custom Python` | **get_style_recommendations**| ✅ |
| **Safety** | `Human-in-the-loop` | **Confirmation Step** | ✅ |

---

## 🚀 Production Readiness & LLMOps (Backlog)

1.  **Evaluation**: Implement `RAGAS` to test answer quality.
2.  **Semantic Caching**: Use `Redis` to save costs on repeat queries.
3.  **Guardrails**: Use `NeMo Guardrails` for price & content safety.
