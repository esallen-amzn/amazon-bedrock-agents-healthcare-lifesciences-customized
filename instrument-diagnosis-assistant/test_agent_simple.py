#!/usr/bin/env python3
"""
Simple test agent without complex dependencies
"""
from strands import Agent
from strands.models import BedrockModel
from strands_tools import current_time
import asyncio

async def test_simple_agent():
    """Test a simple agent with minimal dependencies"""
    try:
        # Create a simple model
        model = BedrockModel(
            model_id="us.amazon.nova-pro-v1:0",
            temperature=0.1,
            max_tokens=1000,
        )
        
        # Create agent with minimal tools
        agent = Agent(
            model=model,
            system_prompt="You are a helpful instrument diagnosis assistant. Respond briefly and clearly.",
            tools=[current_time],
        )
        
        # Test the agent
        print("Testing simple agent...")
        response = ""
        async for chunk in agent.stream_async("Hello, what can you help me with?"):
            if "data" in chunk:
                response += chunk["data"]
                print(chunk["data"], end="", flush=True)
        
        print(f"\n\n✅ Agent responded successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing simple agent: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_simple_agent())
    exit(0 if success else 1)