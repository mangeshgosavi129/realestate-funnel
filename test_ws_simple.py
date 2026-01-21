#!/usr/bin/env python
import asyncio
import websockets
import json
import sys

async def test():
    url = 'ws://127.0.0.1:8000/ws?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0NjcxZjI4YS01YjAyLTQ1OTctYjQ3YS05Yzc3MTRlZmEwNTgiLCJvcmdfaWQiOiI5NzRmOTI4OC0zZTA1LTRjMDAtYjczOC1jOWFjMzliYjQxNjkiLCJleHAiOjE3NzE1OTcwMjh9.Mr-Z45bM9TR-hezrrSjMhrpRPR7x-NSy0b7fe_q1Ddw'
    
    with open('/tmp/ws_result.txt', 'w') as f:
        try:
            f.write('Attempting to connect...\n')
            f.flush()
            
            async with websockets.connect(url) as ws:
                f.write('SUCCESS: Connected to WebSocket!\n')
                f.flush()
                
                # Send a message
                msg = json.dumps({"type": "test", "data": "hello"})
                await ws.send(msg)
                f.write(f'Sent: {msg}\n')
                f.flush()
                
                # Receive response
                response = await asyncio.wait_for(ws.recv(), timeout=3.0)
                f.write(f'Received: {response}\n')
                f.flush()
                
                f.write('\n✅ WebSocket test PASSED!\n')
                return True
                
        except Exception as e:
            f.write(f'ERROR: {type(e).__name__}: {e}\n')
            f.write('\n❌ WebSocket test FAILED!\n')
            f.flush()
            return False

if __name__ == '__main__':
    result = asyncio.run(test())
    sys.exit(0 if result else 1)
