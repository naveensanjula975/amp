import httpx
import asyncio
from datetime import datetime

# A script to test the end-to-end webhook functionality and duplicate deduplication

WEBHOOK_URL = "http://127.0.0.1:8000/webhook"
SECRET = "your_super_secret_webhook_token_here"

async def test_webhook():
    print("--- Starting TradingView Webhook E2E Test ---")
    
    payload = {
      "secret": SECRET,
      "action": "buy",
      "symbol": "ES",
      "quantity": 2,
      "order_type": "market",
      "price": None,
      "stop_loss": 5100.00,
      "take_profit": 5250.00,
      "strategy": "Futures Automated Strategy MVP",
      "timestamp": datetime.utcnow().isoformat()
    }

    async with httpx.AsyncClient() as client:
        # 1. Fire the initial webhook alert
        print("\n[TEST] 1. Firing Initial Webhook Alert...")
        try:
            resp1 = await client.post(WEBHOOK_URL, json=payload)
            print(f"Response Status: {resp1.status_code}")
            print(f"Response Body: {resp1.json()}")
        except httpx.ConnectError:
            print(f"ERROR: Server at {WEBHOOK_URL} is not running. Please start it with 'uvicorn app.main:app' and run this script again.")
            return

        # 2. Fire the EXACT same alert instantly to test memory deduplication
        print("\n[TEST] 2. Firing Duplicate Webhook Alert (Instantly)...")
        resp2 = await client.post(WEBHOOK_URL, json=payload)
        print(f"Response Status: {resp2.status_code}")
        print(f"Response Body: {resp2.json()}")
        assert resp2.json().get("status") == "ignored", "Deduplication failed!"
        
        # 3. Fire a different alert (e.g. sell)
        print("\n[TEST] 3. Firing Different Webhook Alert (SELL)...")
        payload["action"] = "sell"
        resp3 = await client.post(WEBHOOK_URL, json=payload)
        print(f"Response Status: {resp3.status_code}")
        print(f"Response Body: {resp3.json()}")
        
        # 4. Fire an invalid secret alert
        print("\n[TEST] 4. Firing Unauthorized Alert...")
        payload["secret"] = "wrong_secret"
        resp4 = await client.post(WEBHOOK_URL, json=payload)
        print(f"Response Status: {resp4.status_code}")
        print(f"Response Body: {resp4.json()}")
        assert resp4.status_code == 401

if __name__ == "__main__":
    asyncio.run(test_webhook())
