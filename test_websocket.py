import asyncio
import websockets
import json
from datetime import datetime

WS_URL = "ws://127.0.0.1:8000"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0NjcxZjI4YS01YjAyLTQ1OTctYjQ3YS05Yzc3MTRlZmEwNTgiLCJvcmdfaWQiOiI5NzRmOTI4OC0zZTA1LTRjMDAtYjczOC1jOWFjMzliYjQxNjkiLCJleHAiOjE3NzE1OTcwMjh9.Mr-Z45bM9TR-hezrrSjMhrpRPR7x-NSy0b7fe_q1Ddw"

async def test_websocket():
    print("="*60)
    print("  WEBSOCKET CONNECTION TEST")
    print("="*60)
    
    ws_url = f"{WS_URL}/ws?token={TOKEN}"
    print(f"\n🔌 Connecting to: {ws_url}")
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print("✅ WebSocket connected successfully!\n")
            
            # Send first test message
            test_message = {
                "type": "ping",
                "timestamp": datetime.now().isoformat(),
                "data": "Hello from WebSocket test"
            }
            print(f"📤 Sending: {json.dumps(test_message, indent=2)}")
            await websocket.send(json.dumps(test_message))
            
            # Wait for response
            print("\n⏳ Waiting for response...")
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"✅ Received: {response}")
                
                try:
                    response_json = json.loads(response)
                    print(f"\n📦 Parsed JSON response:")
                    print(json.dumps(response_json, indent=2))
                except:
                    pass
                    
            except asyncio.TimeoutError:
                print("⚠️ No response within 5 seconds")
            
            # Send second test message
            test_message2 = {
                "type": "test",
                "action": "echo",
                "payload": {"message": "Testing bidirectional communication", "count": 42}
            }
            print(f"\n📤 Sending second message: {json.dumps(test_message2, indent=2)}")
            await websocket.send(json.dumps(test_message2))
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"✅ Received: {response}")
                try:
                    response_json = json.loads(response)
                    print(f"\n📦 Parsed JSON response:")
                    print(json.dumps(response_json, indent=2))
                except:
                    pass
            except asyncio.TimeoutError:
                print("⚠️ No response within 5 seconds")
            
            print("\n" + "="*60)
            print("  ✅ WEBSOCKET TEST COMPLETED SUCCESSFULLY")
            print("="*60)
            
    except Exception as e:
        print(f"\n❌ WebSocket error: {type(e).__name__}: {e}")
        print("\n" + "="*60)
        print("  ❌ WEBSOCKET TEST FAILED")
        print("="*60)
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_websocket())
    exit(0 if success else 1)
