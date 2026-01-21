import asyncio
import json
import sys
from typing import Any, Dict

import websockets


async def test_websocket_connection(token: str) -> None:
    """
    Connects to FastAPI websocket endpoint at:
      ws://localhost:8000/ws?token=...
    Sends a simple message and prints the response.
    """

    ws_url = f"ws://localhost:8000/ws?token={token}"
    print(f"Connecting to: {ws_url}")

    try:
        async with websockets.connect(ws_url) as websocket:
            print("✅ Connected!")

            # Send a simple JSON payload
            msg: Dict[str, Any] = {
                "event": "ping",
                "payload": {
                    "message": "hello from ws_test_client.py"
                }
            }

            print(f"➡️  Sending: {msg}")
            await websocket.send(json.dumps(msg))

            # Receive response
            response_raw = await websocket.recv()
            try:
                response = json.loads(response_raw)
                print(f"⬅️  Received JSON: {response}")
            except json.JSONDecodeError:
                print(f"⬅️  Received TEXT: {response_raw}")

            print("✅ Test completed successfully.")

    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ Connection rejected with HTTP status: {e.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """
    Usage:
      python ws_test_client.py YOUR_TOKEN

    Example:
      python ws_test_client.py abc123
    """
    if len(sys.argv) < 2:
        print("Usage: python ws_test_client.py <token>")
        print("Example: python ws_test_client.py abc123")
        sys.exit(1)

    token = sys.argv[1]
    asyncio.run(test_websocket_connection(token))


if __name__ == "__main__":
    main()