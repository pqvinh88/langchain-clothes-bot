import streamlit as st
from functools import wraps
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx

from tools import add_to_cart, remove_from_cart, get_style_recommendations, checkout, get_session_state, session_state_var
from retriever import get_ensemble_retriever

def get_chatbot_agent(api_key: str, model_choice: str, shared_state=None):
    if not api_key:
        return None
    
    # Capture the current Streamlit session ID
    ctx = get_script_run_ctx()
    session_id = ctx.session_id if ctx else None
    print(f"[DEBUG] Captured Streamlit session ID: {session_id}")
    
    def wrap_with_context(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if ctx:
                add_script_run_ctx(ctx)
            # We'll also pass session_id to the tool if it's aware of it
            return fn(*args, **kwargs)
        return wrapper

    llm = ChatOpenAI(api_key=api_key, model=model_choice, streaming=True)
    retriever = get_ensemble_retriever(api_key)

    @tool
    def search_clothes(query: str):
        """Searches our product catalog for clothing items. Use this whenever the user asks for suggestions or specific types of clothes."""
        # Set the thread-local storage for state
        if shared_state:
            session_state_var.set(shared_state)
            
        if ctx:
            add_script_run_ctx(ctx)
        
        if not retriever:
            return "Product database is currently unavailable."
        
        docs = retriever.invoke(query)
        results = []
        img_map = {
            "1": "assets/shirt.png",
            "2": "assets/chinos.png",
            "3": "assets/dress.png",
            "4": "assets/jacket.png",
            "5": "assets/sneakers.png"
        }
        
        for doc in docs:
            prod_id = doc.metadata.get("id")
            img_path = doc.metadata.get("image", img_map.get(prod_id, ""))
            
            results.append({
                "name": doc.page_content.split("\n")[0].replace("Name: ", ""),
                "price": doc.metadata.get("price"),
                "image": img_path,
                "description": doc.page_content.split("\n")[1].replace("Description: ", "")
            })
        
        state = shared_state if shared_state is not None else get_session_state()
        state["last_search_results"] = results
        return "\n\n".join([doc.page_content for doc in docs])

    # Wrap imported tools to preserve context in background threads
    # We pass shared_state to the function if it's available
    def inject_state(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # Set the thread-local storage for state
            if shared_state:
                session_state_var.set(shared_state)
                
            if ctx:
                add_script_run_ctx(ctx)
            return fn(*args, **kwargs)
        return wrapper

    wrapped_add_to_cart = tool(inject_state(add_to_cart.func), description=add_to_cart.description)
    wrapped_remove_from_cart = tool(inject_state(remove_from_cart.func), description=remove_from_cart.description)
    wrapped_get_style_recommendations = tool(inject_state(get_style_recommendations.func), description=get_style_recommendations.description)
    wrapped_checkout = tool(inject_state(checkout.func), description=checkout.description)

    tools = [search_clothes, wrapped_add_to_cart, wrapped_remove_from_cart, wrapped_get_style_recommendations, wrapped_checkout]
    
    system_message = """You are an expert Fashion Stylist. 
    
    Your goal is to help users find clothes, manage their cart, and provide style advice. 
    Always be polite. Use 'add_to_cart' when they want to buy, 'remove_from_cart' if they change their mind, 'get_style_recommendations' to help them complete their outfit, and 'checkout' when they are ready to purchase."""

    return create_react_agent(
        llm, 
        tools, 
        prompt=system_message,
        checkpointer=st.session_state["checkpointer"]
    )
