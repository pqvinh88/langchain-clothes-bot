import streamlit as st
from langchain_core.callbacks import BaseCallbackHandler

class TerminalLogHandler(BaseCallbackHandler):
    def on_agent_action(self, action, **kwargs):
        print("\n" + "="*50)
        print("🚀 [STAGE 1: INTENT ROUTING (AGENTIC)]")
        print("="*50)
        print(f"[BE] 🛠️  TOOL CALLED: {action.tool}")
        print(f"[BE] 💭 THOUGHT: {action.log.strip()}")
        print(f"[BE] 📥 INPUT: {action.tool_input}")

    def on_tool_end(self, output, **kwargs):
        print(f"[BE] ✅ RESULT: {output}")
        print("-" * 50)
