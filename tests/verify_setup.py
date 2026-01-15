import sys
import os
import asyncio
from dotenv import load_dotenv

# Add root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

# Load env manually to ensure it is present for the test
load_dotenv()

def data_mode_test():
    print("--- STARTING VERIFICATION ---")
    try:
        from src.core.config import get_settings
        settings = get_settings()
        print(f"✅ Configuration Loaded. Project ID: {settings.PROJECT_ID}")
    except Exception as e:
        print(f"❌ Configuration Failed: {e}")
        sys.exit(1)

    try:
        from src.agents.telesales_agent import TelesalesAgent
        print("Initializing Agent...")
        agent = TelesalesAgent()
        print("✅ Agent Initialized (Mock or Real).")
        
        # Verify Async Method Signature
        import inspect
        if inspect.iscoroutinefunction(agent.generate_pitch):
             print("✅ generate_pitch is ASYNC")
        else:
             print("❌ generate_pitch is NOT ASYNC")
             sys.exit(1)
             
    except Exception as e:
        print(f"❌ Agent Initialization Failed: {e}")
        sys.exit(1)
        
    print("--- VERIFICATION SUCCESS ---")

if __name__ == "__main__":
    data_mode_test()
