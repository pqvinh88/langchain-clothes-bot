import streamlit as st
from langchain_core.tools import tool
from streamlit.runtime import get_instance
from contextvars import ContextVar

# Thread-safe storage for the session state
session_state_var = ContextVar("session_state", default=None)

def get_session_state():
    """Helper to get the session state even in background threads."""
    # 1. Try the ContextVar first (set by the agent wrapper)
    state = session_state_var.get()
    if state is not None:
        return state
        
    # 2. Fallback to standard st.session_state
    try:
        return st.session_state
    except Exception:
        # 3. Deep fallback for background threads using session_id
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        ctx = get_script_run_ctx()
        if ctx:
            runtime = get_instance()
            client = runtime.get_client(ctx.session_id)
            if client:
                return client.session_state
    return {}

@tool
def add_to_cart(item_name: str, price: float):
    """Adds a specific item and its price to the user's shopping cart."""
    state = get_session_state()
    if "cart" not in state:
        state["cart"] = []
    state["cart"].append({"name": item_name, "price": price})
    return f"Successfully added {item_name} (${price}) to the cart."

@tool
def remove_from_cart(item_name: str):
    """Removes an item from the user's shopping cart by its name."""
    state = get_session_state()
    if "cart" not in state:
        state["cart"] = []
    cart = state["cart"]
    initial_len = len(cart)
    state["cart"] = [item for item in cart if item_name.lower() not in item["name"].lower()]
    if len(state["cart"]) < initial_len:
        return f"Successfully removed {item_name} from the cart."
    return f"Could not find {item_name} in your cart."

@tool
def get_style_recommendations(item_name: str):
    """Provides fashion advice on what items pair well with a specific piece of clothing."""
    recommendations = {
        "shirt": "These pair perfectly with our Slim-Fit Black Chinos for a classic look.",
        "dress": "I recommend matching this with a pair of Minimalist White Sneakers for a trendy, casual vibe.",
        "jacket": "This goes great with any of our rugged outdoor pants.",
        "sneakers": "These are versatile! They work with both our Chinos and our Summer Dresses."
    }
    for key, advice in recommendations.items():
        if key in item_name.lower():
            return advice
    return "This is a versatile piece! I'd recommend keeping the rest of the outfit simple to let it stand out."

@tool
def checkout(confirmed: bool = False):
    """Processes the checkout for the items in the shopping cart. 
    IMPORTANT: You MUST ask the user 'Are you sure you want to checkout?' and ONLY set confirmed=True if they have explicitly confirmed.
    If they haven't confirmed yet, call this tool with confirmed=False to show the approval button.
    """
    state = get_session_state()
    if not confirmed:
        state["needs_approval"] = "checkout"
        return "I've prepared your order. Please confirm by clicking the 'Confirm Purchase' button above or by saying 'Yes'!"

    if not state.get("cart"):
        return "Your cart is empty. Please add some items before trying to check out."
    
    items = state["cart"]
    total = sum(item['price'] for item in items)
    item_list = ", ".join([item['name'] for item in items])
    
    state["last_order"] = {
        "items": items.copy(),
        "total": total
    }
    
    state["cart"] = [] # Clear the cart
    if "needs_approval" in state:
        del state["needs_approval"]
    return f"Checkout completed successfully! Total: ${total:.2f}. Items: {item_list}. Your order is being processed."
