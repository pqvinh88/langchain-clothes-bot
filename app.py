import streamlit as st
from langchain_classic.memory import ConversationBufferMemory
from langchain_classic.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.tools import tool
from langchain_core.tools.retriever import create_retriever_tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
import os
from dotenv import load_dotenv
from langchain_core.callbacks import BaseCallbackHandler

# Custom Callback for Backend (BE) Logging
class TerminalLogHandler(BaseCallbackHandler):
    def on_agent_action(self, action, **kwargs):
        print(f"\n[BE] 🛠️  TOOL CALLED: {action.tool}")
        print(f"[BE] 💭 THOUGHT: {action.log.strip()}")
        print(f"[BE] 📥 INPUT: {action.tool_input}")

    def on_tool_end(self, output, **kwargs):
        print(f"[BE] ✅ RESULT: {output}")
        print("-" * 30)

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(page_title="ClothesBot AI", page_icon="👕", layout="wide")

# Custom CSS for a premium feel
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stChatMessage {
        border-radius: 15px;
        padding: 10px;
        margin-bottom: 10px;
    }
    .stChatInput {
        border-radius: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar for configuration
with st.sidebar:
    st.title("👕 ClothesBot AI")
    st.markdown("---")
    api_key = st.text_input("Enter OpenAI API Key", type="password")
    model_choice = st.selectbox("Choose Model", ["gpt-4o", "gpt-4o-mini"])
    st.markdown("---")
    if st.button("Clear Conversation"):
        st.session_state.messages = []
        st.session_state.memory.clear()
        st.session_state.cart = []
        st.rerun()
    
    st.markdown("---")
    st.subheader("🛒 Your Shopping Cart")
    if "last_order" in st.session_state and not st.session_state.cart:
        st.success("✨ Last order successful!")
    
    if not st.session_state.get("cart"):
        st.info("Your cart is empty.")
    else:
        total = 0
        for i, item in enumerate(st.session_state.cart):
            st.write(f"{i+1}. {item['name']} - **${item['price']}**")
            total += item['price']
        st.markdown(f"**Total: ${total:.2f}**")
        if st.button("Proceed to Checkout"):
            if not st.session_state.cart:
                st.error("Cart is empty!")
            else:
                # We can trigger the checkout logic here as well
                total = sum(item['price'] for item in st.session_state.cart)
                st.session_state.last_order = {
                    "items": st.session_state.cart.copy(),
                    "total": total
                }
                st.session_state.cart = []
                st.success(f"Order placed! Total: ${total:.2f}")
                st.balloons()
                st.rerun()

# Initialize session state for memory and messages
if "messages" not in st.session_state:
    st.session_state.messages = []

if "cart" not in st.session_state:
    st.session_state.cart = []

# Ensure memory is initialized with the correct keys for Agent
if "memory" not in st.session_state or getattr(st.session_state.memory, "output_key", None) != "output":
    st.session_state.memory = ConversationBufferMemory(
        memory_key="chat_history", 
        return_messages=True,
        input_key="input",
        output_key="output"
    )

# --- TOOL DEFINITIONS ---

@tool
def add_to_cart(item_name: str, price: float):
    """Adds a specific item and its price to the user's shopping cart."""
    st.session_state.cart.append({"name": item_name, "price": price})
    return f"Successfully added {item_name} (${price}) to the cart."

@tool
def remove_from_cart(item_name: str):
    """Removes an item from the user's shopping cart by its name."""
    initial_len = len(st.session_state.cart)
    st.session_state.cart = [item for item in st.session_state.cart if item_name.lower() not in item["name"].lower()]
    if len(st.session_state.cart) < initial_len:
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
    if not confirmed:
        st.session_state.needs_approval = "checkout"
        return "I've prepared your order. Please confirm by clicking the 'Confirm Purchase' button above or by saying 'Yes'!"

    if not st.session_state.get("cart"):
        return "Your cart is empty. Please add some items before trying to check out."
    
    items = st.session_state.cart
    total = sum(item['price'] for item in items)
    item_list = ", ".join([item['name'] for item in items])
    
    # Store order info in session state to display a nice confirmation
    st.session_state.last_order = {
        "items": items.copy(),
        "total": total
    }
    
    st.session_state.cart = [] # Clear the cart
    if "needs_approval" in st.session_state:
        del st.session_state.needs_approval
    return f"Checkout completed successfully! Total: ${total:.2f}. Items: {item_list}. Your order is being processed."

# Helper to initialize the Agent
def get_chatbot_agent():
    if not api_key:
        st.error("Please enter your OpenAI API Key in the sidebar.")
        return None
    
    llm = ChatOpenAI(api_key=api_key, model=model_choice, streaming=True)
    
    # 1. Setup Retriever Tool
    if os.path.exists("./chroma_db"):
        embeddings = OpenAIEmbeddings(api_key=api_key)
        vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
        
        # Custom Search Tool to capture metadata for UI
        @tool
        def search_clothes(query: str):
            """Searches our product catalog for clothing items. Use this whenever the user asks for suggestions or specific types of clothes."""
            docs = retriever.invoke(query)
            results = []
            for doc in docs:
                # Add image path mapping if not in metadata
                img_map = {
                    "1": "assets/shirt.png",
                    "2": "assets/chinos.png",
                    "3": "assets/dress.png",
                    "4": "assets/jacket.png",
                    "5": "assets/sneakers.png"
                }
                prod_id = doc.metadata.get("id")
                img_path = doc.metadata.get("image", img_map.get(prod_id, ""))
                
                results.append({
                    "name": doc.page_content.split("\n")[0].replace("Name: ", ""),
                    "price": doc.metadata.get("price"),
                    "image": img_path,
                    "description": doc.page_content.split("\n")[1].replace("Description: ", "")
                })
            st.session_state.last_search_results = results
            return "\n\n".join([doc.page_content for doc in docs])

        tools = [search_clothes, add_to_cart, remove_from_cart, get_style_recommendations, checkout]
    else:
        st.warning("Product database not found. Run 'python ingest_products.py' to enable search.")
        # Define a fallback search tool that does nothing if DB is missing
        @tool
        def search_clothes(query: str):
            """Searches catalog."""
            return "Product database is currently unavailable."
        tools = [search_clothes, add_to_cart, remove_from_cart, get_style_recommendations, checkout]

    # 2. Setup Agent Prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert Fashion Stylist. 
        
        CRITICAL INSTRUCTION: Before using any tool, state your 'Internal Thought' about why you are choosing that tool.
        Example: 'Thought: The user wants a dress, so I will search the catalog for available dresses.'
        
        Your goal is to help users find clothes, manage their cart, and provide style advice. 
        Always be polite. Use 'add_to_cart' when they want to buy, 'remove_from_cart' if they change their mind, 'get_style_recommendations' to help them complete their outfit, and 'checkout' when they are ready to purchase."""),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    # 3. Create Agent
    agent = create_openai_tools_agent(llm, tools, prompt)
    return AgentExecutor(
        agent=agent, 
        tools=tools, 
        memory=st.session_state.memory, 
        verbose=True,
        return_intermediate_steps=True
    )

# UI Header
st.title("Style Assistant")
st.caption("Your personal e-commerce fashion expert, powered by LangChain.")

# Display last order confirmation if it exists
if "last_order" in st.session_state:
    with st.expander("📄 View Last Order Confirmation", expanded=True):
        order = st.session_state.last_order
        st.success(f"Order processed for **${order['total']:.2f}**")
        for item in order['items']:
            st.write(f"- {item['name']} (${item['price']})")
        if st.button("Close Confirmation"):
            del st.session_state.last_order
            st.rerun()

# Human-in-the-loop Approval UI
if st.session_state.get("needs_approval"):
    with st.warning("🛡️ **Action Requires Your Approval**"):
        col1, col2 = st.columns(2)
        if col1.button("✅ Confirm Purchase", use_container_width=True):
            # We trigger a special message to the agent to finalize
            st.session_state.messages.append({"role": "user", "content": "I confirm the purchase."})
            del st.session_state.needs_approval
            st.rerun()
        if col2.button("❌ Cancel", use_container_width=True):
            del st.session_state.needs_approval
            st.rerun()

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("How can I help you find the perfect outfit today?"):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate AI response
    agent_executor = get_chatbot_agent()
    if agent_executor:
        with st.chat_message("assistant"):
            # 1. Logic & Knowledge Log (Collapsible)
            log_placeholder = st.expander("🔍 View Knowledge & Thought Log")
            response_placeholder = st.empty()
            
            # Use invoke for AgentExecutor with intermediate steps and BE callback
            response = agent_executor.invoke(
                {"input": prompt},
                config={"callbacks": [TerminalLogHandler()]}
            )
            full_response = response["output"]
            steps = response.get("intermediate_steps", [])
            
            # Display logic in the log and print to terminal
            with log_placeholder:
                if not steps:
                    st.write("No tools needed for this response.")
                    print("\n--- No tools needed for this response ---")
                for i, (action, observation) in enumerate(steps):
                    # UI Log
                    st.markdown(f"🤖 **Action {i+1}: `{action.tool}`**")
                    with st.status(f"Running `{action.tool}`...", expanded=False):
                        st.write(f"**Reasoning:** {action.log}")
                        st.write(f"**Input Data:** `{action.tool_input}`")
                    
                    st.markdown("**🧠 Knowledge Retrieved:**")
                    st.info(observation)
            
            # Display final answer
            response_placeholder.markdown(full_response)
            
            # Stage 3.1: Visual Product Cards
            if st.session_state.get("last_search_results"):
                with st.container():
                    st.markdown("### 🛍️ Recommended Products")
                    cols = st.columns(len(st.session_state.last_search_results))
                    for i, product in enumerate(st.session_state.last_search_results):
                        with cols[i]:
                            if product["image"]:
                                st.image(product["image"], use_container_width=True)
                            st.markdown(f"**{product['name']}**")
                            st.markdown(f"💰 ${product['price']}")
                            if st.button(f"Add to Cart", key=f"btn_{product['name']}_{i}"):
                                st.session_state.cart.append({"name": product["name"], "price": product["price"]})
                                st.toast(f"Added {product['name']} to cart!")
                                st.rerun()
                # Clear results after displaying so they don't persist incorrectly
                del st.session_state.last_search_results
            
        # Add assistant message to history BEFORE potential rerun
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        
        # Force a rerun to update the sidebar cart view immediately after tool calls
        if any(word in full_response.lower() for word in ["added", "removed", "completed", "success"]):
            st.rerun()
