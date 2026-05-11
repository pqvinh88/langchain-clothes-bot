import streamlit as st
import os
from dotenv import load_dotenv
from langgraph.checkpoint.memory import MemorySaver

# Local imports
from utils import TerminalLogHandler
from agent import get_chatbot_agent

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(page_title="ClothesBot AI", page_icon="👕", layout="wide")

# Initialize session state for memory, messages, and cart
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "cart" not in st.session_state:
    st.session_state["cart"] = []
if "checkpointer" not in st.session_state:
    st.session_state["checkpointer"] = MemorySaver()

# Custom CSS for a premium feel
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stChatMessage { border-radius: 15px; padding: 10px; margin-bottom: 10px; }
    .stChatInput { border-radius: 20px; }
    </style>
""", unsafe_allow_html=True)

# Sidebar for configuration
with st.sidebar:
    st.title("👕 ClothesBot AI")
    st.markdown("---")
    api_key = st.text_input("Enter OpenAI API Key", type="password")
    model_choice = st.selectbox("Choose Model", ["gpt-4o-mini", "gpt-4o"])
    st.markdown("---")
    
    if st.button("Clear Conversation"):
        st.session_state["messages"] = []
        st.session_state["checkpointer"] = MemorySaver()
        st.session_state["cart"] = []
        st.rerun()
    
    st.markdown("---")
    st.subheader("🛒 Your Shopping Cart")
    if "last_order" in st.session_state and not st.session_state["cart"]:
        st.success("✨ Last order successful!")
    
    if not st.session_state.get("cart"):
        st.info("Your cart is empty.")
    else:
        total = 0
        for i, item in enumerate(st.session_state["cart"]):
            st.write(f"{i+1}. {item['name']} - **${item['price']}**")
            total += item['price']
        st.markdown(f"**Total: ${total:.2f}**")
        
        if st.button("Proceed to Checkout"):
            if not st.session_state["cart"]:
                st.error("Cart is empty!")
            else:
                total = sum(item['price'] for item in st.session_state["cart"])
                st.session_state["last_order"] = {"items": st.session_state["cart"].copy(), "total": total}
                st.session_state["cart"] = []
                st.success(f"Order placed! Total: ${total:.2f}")
                st.balloons()
                st.rerun()

# UI Header
st.title("Style Assistant")
st.caption("Your personal e-commerce fashion expert, powered by LangChain.")

# Display last order confirmation
if "last_order" in st.session_state:
    with st.expander("📄 View Last Order Confirmation", expanded=True):
        order = st.session_state["last_order"]
        st.success(f"Order processed for **${order['total']:.2f}**")
        for item in order['items']:
            st.write(f"- {item['name']} (${item['price']})")
        if st.button("Close Confirmation"):
            del st.session_state["last_order"]
            st.rerun()

# Human-in-the-loop Approval UI
if st.session_state.get("needs_approval"):
    with st.warning("🛡️ **Action Requires Your Approval**"):
        col1, col2 = st.columns(2)
        if col1.button("✅ Confirm Purchase", use_container_width=True):
            st.session_state["messages"].append({"role": "user", "content": "I confirm the purchase."})
            del st.session_state["needs_approval"]
            st.rerun()
        if col2.button("❌ Cancel", use_container_width=True):
            del st.session_state["needs_approval"]
            st.rerun()

# Display chat history
for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("How can I help you find the perfect outfit today?"):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    agent_executor = get_chatbot_agent(api_key, model_choice, st.session_state)
    if agent_executor:
        with st.chat_message("assistant"):
            log_placeholder = st.expander("🔍 View Knowledge & Thought Log")
            response_placeholder = st.empty()
            
            state = agent_executor.invoke(
                {"messages": [("user", prompt)]},
                config={"configurable": {"thread_id": "session"}, "callbacks": [TerminalLogHandler()]}
            )
            
            full_response = state["messages"][-1].content
            
            # Parse tool calls for logs
            tool_calls = []
            tool_results = {}
            print(f"state: {state}")
            for msg in state["messages"]:
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for call in msg.tool_calls:
                        tool_calls.append(call)
                if msg.type == "tool":
                    tool_results[msg.tool_call_id] = msg.content
            
            with log_placeholder:
                if not tool_calls:
                    st.write("No tools needed for this response.")
                for i, call in enumerate(tool_calls):
                    st.markdown(f"🤖 **Action {i+1}: `{call['name']}`**")
                    with st.status(f"Running `{call['name']}`...", expanded=False):
                        st.write(f"**Input Data:** `{call['args']}`")
                    st.info(tool_results.get(call.get("id"), "Executed"))
            
            response_placeholder.markdown(full_response)
            
            if st.session_state.get("last_search_results"):
                with st.container():
                    st.markdown("### 🛍️ Recommended Products")
                    cols = st.columns(len(st.session_state["last_search_results"]))
                    for i, product in enumerate(st.session_state["last_search_results"]):
                        with cols[i]:
                            if product["image"]:
                                st.image(product["image"], use_container_width=True)
                            st.markdown(f"**{product['name']}**")
                            st.markdown(f"💰 ${product['price']}")
                            if st.button(f"Add to Cart", key=f"btn_{product['name']}_{i}"):
                                st.session_state["cart"].append({"name": product["name"], "price": product["price"]})
                                st.toast(f"Added {product['name']} to cart!")
                                st.rerun()
                del st.session_state["last_search_results"]
            
        st.session_state["messages"].append({"role": "assistant", "content": full_response})
        
        mutating_tools = {"add_to_cart", "remove_from_cart", "checkout"}
        state_mutated = any(call["name"] in mutating_tools for call in tool_calls)
        
        if st.session_state.get("needs_approval") or state_mutated:
            st.rerun()
