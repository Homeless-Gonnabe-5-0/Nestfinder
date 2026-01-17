# agents/conversation.py - Natural Conversation Agent using Ollama

import os
import sys
import json
import re
import httpx
from typing import Optional
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

# Simple prompt - let the AI be natural
SYSTEM_PROMPT = """You are Nestfinder, a friendly assistant helping people find apartments in Ottawa.

Rules:
- Be natural and conversational
- Keep responses short (1-3 sentences)
- If someone asks about apartments, say you'll search for them
- NEVER make up apartment listings or prices - you don't have that data
- If you don't know something, say so honestly
- Ottawa neighborhoods include: Centretown, Byward Market, The Glebe, Westboro, Hintonburg, Sandy Hill, Little Italy, Vanier"""


class ConversationAgent:
    """Natural conversation using Ollama + smart intent detection."""
    
    def __init__(self):
        self.name = "ConversationAgent"
        self.base_url = OLLAMA_BASE_URL
        self.model = OLLAMA_MODEL
        self.client = httpx.AsyncClient(timeout=60.0)
        self.conversations: dict[str, list] = {}
        print(f"[{self.name}] initialized with Ollama ({self.model})")
    
    def _detect_search_intent(self, message: str) -> Optional[dict]:
        """
        Detect if user wants to search for apartments.
        Returns extracted params or None.
        """
        msg = message.lower()
        
        # Check for search-related keywords
        search_triggers = ["find", "search", "show", "looking for", "need", "want", 
                          "apartment", "place", "rent", "bedroom", "bed", "studio"]
        
        has_search_intent = any(trigger in msg for trigger in search_triggers)
        
        # Also check for price mentions
        has_price = bool(re.search(r'\$\d+|\d+\s*(dollars|bucks|/month|per month)', msg))
        
        if not (has_search_intent or has_price):
            return None
        
        # Extract parameters from the message
        params = {
            "budget_min": 0,
            "budget_max": 3000,
            "bedrooms": 1,
            "work_address": "",
            "priorities": ["short_commute"],
            "max_commute_minutes": 45,
            "transport_mode": "transit"
        }
        
        # Extract budget
        price_match = re.search(r'under\s*\$?(\d+)', msg)
        if price_match:
            params["budget_max"] = int(price_match.group(1))
        
        price_range = re.search(r'\$?(\d+)\s*[-–to]+\s*\$?(\d+)', msg)
        if price_range:
            params["budget_min"] = int(price_range.group(1))
            params["budget_max"] = int(price_range.group(2))
        
        # Extract bedrooms
        bed_match = re.search(r'(\d+)\s*[-\s]?(bed|bedroom|br)', msg)
        if bed_match:
            params["bedrooms"] = int(bed_match.group(1))
        elif "studio" in msg:
            params["bedrooms"] = 0
        
        # Extract work location
        work_patterns = [
            r'(?:near|close to|by|at)\s+([^,.\n]+?)(?:\s+for|\s+under|\s+with|$)',
            r'commute to\s+([^,.\n]+)',
            r'work (?:at|near)\s+([^,.\n]+)'
        ]
        for pattern in work_patterns:
            match = re.search(pattern, msg, re.IGNORECASE)
            if match:
                params["work_address"] = match.group(1).strip()
                break
        
        # Extract priorities
        priorities = []
        if any(w in msg for w in ["safe", "safety", "secure"]):
            priorities.append("safe_area")
        if any(w in msg for w in ["walk", "walkable"]):
            priorities.append("walkable")
        if any(w in msg for w in ["quiet", "peaceful"]):
            priorities.append("quiet")
        if any(w in msg for w in ["cheap", "affordable", "budget"]):
            priorities.append("low_price")
        if any(w in msg for w in ["transit", "bus", "train"]):
            priorities.append("good_transit")
        if priorities:
            params["priorities"] = priorities
        
        return params
    
    def _get_conversation(self, session_id: str) -> list:
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        return self.conversations[session_id]
    
    def _add_to_history(self, session_id: str, role: str, content: str):
        history = self._get_conversation(session_id)
        history.append({"role": role, "content": content})
        if len(history) > 10:
            self.conversations[session_id] = history[-10:]
    
    async def chat(
        self,
        message: str,
        session_id: str = "default",
        pinned_location: Optional[tuple] = None
    ) -> dict:
        """Process message and return response."""
        
        # First, check if this is a search request
        search_params = self._detect_search_intent(message)
        
        if search_params:
            # Add pinned location if available
            if pinned_location:
                search_params["pinned_lat"] = pinned_location[0]
                search_params["pinned_lng"] = pinned_location[1]
            
            # Get a natural response from Ollama
            ai_response = await self._get_ollama_response(
                f"User wants to search for apartments: '{message}'. Give a brief, friendly acknowledgment (1 sentence). Don't list any apartments.",
                session_id
            )
            
            return {
                "response": ai_response,
                "search_params": search_params,
                "intent": "search"
            }
        
        # Regular chat - let Ollama handle it naturally
        ai_response = await self._get_ollama_response(message, session_id)
        
        return {
            "response": ai_response,
            "search_params": None,
            "intent": "chat"
        }
    
    async def _get_ollama_response(self, message: str, session_id: str) -> str:
        """Get response from Ollama."""
        
        history = self._get_conversation(session_id)
        
        # Build prompt
        prompt = SYSTEM_PROMPT + "\n\n"
        for msg in history[-4:]:
            role = "User" if msg["role"] == "user" else "Assistant"
            prompt += f"{role}: {msg['content']}\n"
        prompt += f"User: {message}\nAssistant:"
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 80,  # Shorter responses = faster
                        "top_k": 20,        # Faster sampling
                        "top_p": 0.9
                    }
                }
            )
            
            if response.status_code != 200:
                return "Hey! How can I help you find an apartment today?"
            
            result = response.json()
            ai_response = result.get("response", "").strip()
            
            # Store in history
            self._add_to_history(session_id, "user", message)
            self._add_to_history(session_id, "assistant", ai_response)
            
            return ai_response if ai_response else "Hey! What are you looking for?"
            
        except httpx.ConnectError:
            return "I'm having trouble thinking right now. Make sure Ollama is running!"
        except Exception as e:
            print(f"[{self.name}] Error: {e}")
            return "Something went wrong on my end. What were you looking for?"
    
    def clear_history(self, session_id: str):
        if session_id in self.conversations:
            del self.conversations[session_id]


if __name__ == "__main__":
    import asyncio
    
    async def test():
        agent = ConversationAgent()
        
        print("\n=== Testing ConversationAgent ===\n")
        
        # Test greeting
        r = await agent.chat("yo")
        print(f"User: yo")
        print(f"Bot: {r['response']}")
        print(f"Intent: {r['intent']}\n")
        
        # Test search
        r = await agent.chat("find me a 2 bedroom under $2000")
        print(f"User: find me a 2 bedroom under $2000")
        print(f"Bot: {r['response']}")
        print(f"Intent: {r['intent']}")
        print(f"Params: {r['search_params']}\n")
        
        # Test question
        r = await agent.chat("what neighborhoods are safe?")
        print(f"User: what neighborhoods are safe?")
        print(f"Bot: {r['response']}")
        print(f"Intent: {r['intent']}")
    
    asyncio.run(test())
