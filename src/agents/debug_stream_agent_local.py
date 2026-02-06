import asyncio
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.agents.telesales_agent import TelesalesAgent

async def debug_stream():
    print("--- Starting Debug Stream ---")
    agent = TelesalesAgent()
    
    # Mock user message that triggers a tool call
    user_message = "me informe um cliente sem compras a mais de 90 dias"
    vendor_filter = "Vendedor Teste"

    print(f"Message: {user_message}")
    
    try:
        async for chunk in agent.chat_stream(user_message, vendor_filter=vendor_filter):
            print(f"Received Chunk: {chunk}")
    except Exception as e:
        print(f"!!! CAUGHT EXCEPTION IN MAIN LOOP: {e}")

if __name__ == "__main__":
    asyncio.run(debug_stream())
