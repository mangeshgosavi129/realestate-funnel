import requests
import json
import asyncio
import websockets
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"
WS_URL = "ws://127.0.0.1:8000"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0NjcxZjI4YS01YjAyLTQ1OTctYjQ3YS05Yzc3MTRlZmEwNTgiLCJvcmdfaWQiOiI5NzRmOTI4OC0zZTA1LTRjMDAtYjczOC1jOWFjMzliYjQxNjkiLCJleHAiOjE3NzE1OTcwMjh9.Mr-Z45bM9TR-hezrrSjMhrpRPR7x-NSy0b7fe_q1Ddw"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_result(endpoint, status, response_text):
    print(f"\n📍 Endpoint: {endpoint}")
    print(f"✅ Status: {status}" if 200 <= status < 300 else f"❌ Status: {status}")
    try:
        response_json = json.loads(response_text)
        print(f"📦 Response: {json.dumps(response_json, indent=2)}")
    except:
        print(f"📦 Response: {response_text}")

# =========================================================
# AUTHENTICATION TESTS
# =========================================================
def test_auth():
    print_section("AUTHENTICATION TESTS")
    
    # Test Login (will fail with test credentials, but tests endpoint)
    print("\n🔐 Testing Login...")
    try:
        payload = {"email": "test@example.com", "password": "testpass"}
        response = requests.post(f"{BASE_URL}/auth/login", json=payload)
        print_result("POST /auth/login", response.status_code, response.text)
    except Exception as e:
        print(f"❌ Error: {e}")

# =========================================================
# DASHBOARD TESTS
# =========================================================
def test_dashboard():
    print_section("DASHBOARD TESTS")
    
    print("\n📊 Testing Dashboard Stats...")
    try:
        response = requests.get(f"{BASE_URL}/dashboard/stats", headers=headers)
        print_result("GET /dashboard/stats", response.status_code, response.text)
    except Exception as e:
        print(f"❌ Error: {e}")

# =========================================================
# LEADS TESTS
# =========================================================
def test_leads():
    print_section("LEADS TESTS")
    
    # Get all leads
    print("\n👥 Testing Get All Leads...")
    try:
        response = requests.get(f"{BASE_URL}/leads/", headers=headers)
        print_result("GET /leads/", response.status_code, response.text)
        
        # Store lead_id for update/delete tests
        if response.status_code == 200:
            leads = response.json()
            if leads:
                lead_id = leads[0].get("id")
                return lead_id
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Create a new lead
    print("\n➕ Testing Create Lead...")
    try:
        payload = {
            "name": "Test Lead",
            "phone": "+1234567890",
            "email": "testlead@example.com",
            "status": "new"
        }
        response = requests.post(f"{BASE_URL}/leads/", headers=headers, json=payload)
        print_result("POST /leads/", response.status_code, response.text)
        
        if response.status_code == 200:
            lead_id = response.json().get("id")
            
            # Update the lead
            print("\n✏️ Testing Update Lead...")
            update_payload = {
                "name": "Updated Test Lead",
                "status": "contacted"
            }
            response = requests.put(f"{BASE_URL}/leads/{lead_id}", headers=headers, json=update_payload)
            print_result(f"PUT /leads/{lead_id}", response.status_code, response.text)
            
            # Delete the lead
            print("\n🗑️ Testing Delete Lead...")
            response = requests.delete(f"{BASE_URL}/leads/{lead_id}", headers=headers)
            print_result(f"DELETE /leads/{lead_id}", response.status_code, response.text)
    except Exception as e:
        print(f"❌ Error: {e}")

# =========================================================
# CONVERSATIONS TESTS
# =========================================================
def test_conversations():
    print_section("CONVERSATIONS TESTS")
    
    print("\n💬 Testing Get All Conversations...")
    try:
        response = requests.get(f"{BASE_URL}/conversations/", headers=headers)
        print_result("GET /conversations/", response.status_code, response.text)
        
        if response.status_code == 200:
            conversations = response.json()
            if conversations:
                conv_id = conversations[0].get("id")
                
                # Get messages for conversation
                print("\n📨 Testing Get Conversation Messages...")
                response = requests.get(f"{BASE_URL}/conversations/{conv_id}/messages", headers=headers)
                print_result(f"GET /conversations/{conv_id}/messages", response.status_code, response.text)
                
                # Test takeover
                print("\n🎯 Testing Conversation Takeover...")
                response = requests.post(f"{BASE_URL}/conversations/{conv_id}/takeover", headers=headers)
                print_result(f"POST /conversations/{conv_id}/takeover", response.status_code, response.text)
                
                # Test release
                print("\n🔓 Testing Conversation Release...")
                response = requests.post(f"{BASE_URL}/conversations/{conv_id}/release", headers=headers)
                print_result(f"POST /conversations/{conv_id}/release", response.status_code, response.text)
    except Exception as e:
        print(f"❌ Error: {e}")

# =========================================================
# MESSAGES TESTS
# =========================================================
def test_messages():
    print_section("MESSAGES TESTS")
    
    print("\n📤 Testing Send Message...")
    try:
        payload = {
            "conversation_id": "test-conv-id",
            "content": "Test message from API test",
            "message_type": "text"
        }
        response = requests.post(f"{BASE_URL}/messages/send", headers=headers, json=payload)
        print_result("POST /messages/send", response.status_code, response.text)
    except Exception as e:
        print(f"❌ Error: {e}")

# =========================================================
# CTAs TESTS
# =========================================================
def test_ctas():
    print_section("CTAs TESTS")
    
    # Get all CTAs
    print("\n🎯 Testing Get All CTAs...")
    try:
        response = requests.get(f"{BASE_URL}/ctas/", headers=headers)
        print_result("GET /ctas/", response.status_code, response.text)
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Create a new CTA
    print("\n➕ Testing Create CTA...")
    try:
        payload = {
            "name": "Test CTA",
            "cta_type": "book_call"
        }
        response = requests.post(f"{BASE_URL}/ctas/", headers=headers, json=payload)
        print_result("POST /ctas/", response.status_code, response.text)
        
        if response.status_code == 200:
            cta_id = response.json().get("id")
            
            # Update the CTA
            print("\n✏️ Testing Update CTA...")
            update_payload = {
                "name": "Updated Test CTA",
                "cta_type": "schedule_demo"
            }
            response = requests.put(f"{BASE_URL}/ctas/{cta_id}", headers=headers, json=update_payload)
            print_result(f"PUT /ctas/{cta_id}", response.status_code, response.text)
            
            # Delete the CTA
            print("\n🗑️ Testing Delete CTA...")
            response = requests.delete(f"{BASE_URL}/ctas/{cta_id}", headers=headers)
            print_result(f"DELETE /ctas/{cta_id}", response.status_code, response.text)
    except Exception as e:
        print(f"❌ Error: {e}")

# =========================================================
# TEMPLATES TESTS
# =========================================================
def test_templates():
    print_section("TEMPLATES TESTS")
    
    # Get all templates
    print("\n📝 Testing Get All Templates...")
    try:
        response = requests.get(f"{BASE_URL}/templates/", headers=headers)
        print_result("GET /templates/", response.status_code, response.text)
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Create a new template
    print("\n➕ Testing Create Template...")
    try:
        payload = {
            "name": "test_template",
            "content": "Hello {{name}}, this is a test template!",
            "category": "marketing",
            "language": "en"
        }
        response = requests.post(f"{BASE_URL}/templates/", headers=headers, json=payload)
        print_result("POST /templates/", response.status_code, response.text)
        
        if response.status_code == 200:
            template_id = response.json().get("id")
            
            # Update the template
            print("\n✏️ Testing Update Template...")
            update_payload = {
                "name": "updated_test_template",
                "content": "Hello {{name}}, this is an updated test template!"
            }
            response = requests.put(f"{BASE_URL}/templates/{template_id}", headers=headers, json=update_payload)
            print_result(f"PUT /templates/{template_id}", response.status_code, response.text)
            
            # Get template status
            print("\n📊 Testing Get Template Status...")
            response = requests.get(f"{BASE_URL}/templates/{template_id}/status", headers=headers)
            print_result(f"GET /templates/{template_id}/status", response.status_code, response.text)
            
            # Delete the template
            print("\n🗑️ Testing Delete Template...")
            response = requests.delete(f"{BASE_URL}/templates/{template_id}", headers=headers)
            print_result(f"DELETE /templates/{template_id}", response.status_code, response.text)
    except Exception as e:
        print(f"❌ Error: {e}")

# =========================================================
# ANALYTICS TESTS
# =========================================================
def test_analytics():
    print_section("ANALYTICS TESTS")
    
    print("\n📈 Testing Get Analytics...")
    try:
        response = requests.get(f"{BASE_URL}/analytics/", headers=headers)
        print_result("GET /analytics/", response.status_code, response.text)
    except Exception as e:
        print(f"❌ Error: {e}")

# =========================================================
# SETTINGS TESTS
# =========================================================
def test_settings():
    print_section("SETTINGS TESTS")
    
    # Get WhatsApp status
    print("\n📱 Testing Get WhatsApp Status...")
    try:
        response = requests.get(f"{BASE_URL}/settings/whatsapp/status", headers=headers)
        print_result("GET /settings/whatsapp/status", response.status_code, response.text)
    except Exception as e:
        print(f"❌ Error: {e}")

# =========================================================
# WEBSOCKET TESTS
# =========================================================
async def test_websocket():
    print_section("WEBSOCKET TESTS")
    
    print("\n🔌 Testing WebSocket Connection...")
    ws_url = f"{WS_URL}/ws?token={TOKEN}"
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print(f"✅ WebSocket connected successfully!")
            
            # Send a test message
            test_message = {
                "type": "ping",
                "timestamp": datetime.now().isoformat(),
                "data": "Hello from test client"
            }
            print(f"\n📤 Sending test message: {json.dumps(test_message, indent=2)}")
            await websocket.send(json.dumps(test_message))
            
            # Wait for response
            print("\n⏳ Waiting for response...")
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"✅ Received response: {response}")
                
                # Try to parse as JSON
                try:
                    response_json = json.loads(response)
                    print(f"📦 Parsed response: {json.dumps(response_json, indent=2)}")
                except:
                    pass
                    
            except asyncio.TimeoutError:
                print("⚠️ No response received within timeout")
            
            # Send another message to test bidirectional communication
            test_message2 = {
                "type": "test",
                "action": "echo",
                "payload": {"message": "Testing bidirectional communication"}
            }
            print(f"\n📤 Sending second test message: {json.dumps(test_message2, indent=2)}")
            await websocket.send(json.dumps(test_message2))
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"✅ Received response: {response}")
                try:
                    response_json = json.loads(response)
                    print(f"📦 Parsed response: {json.dumps(response_json, indent=2)}")
                except:
                    pass
            except asyncio.TimeoutError:
                print("⚠️ No response received within timeout")
            
            print("\n✅ WebSocket test completed successfully!")
            
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ WebSocket connection failed with status code: {e.status_code}")
        print(f"   Headers: {e.headers}")
    except Exception as e:
        print(f"❌ WebSocket error: {type(e).__name__}: {e}")

# =========================================================
# MAIN TEST RUNNER
# =========================================================
def main():
    print("\n" + "="*60)
    print("  🚀 WHATSAPP BOT API & WEBSOCKET TEST SUITE")
    print("="*60)
    print(f"\n📍 Base URL: {BASE_URL}")
    print(f"🔐 Using Token: {TOKEN[:50]}...")
    print(f"⏰ Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run HTTP API tests
    test_auth()
    test_dashboard()
    test_leads()
    test_conversations()
    test_messages()
    test_ctas()
    test_templates()
    test_analytics()
    test_settings()
    
    # Run WebSocket tests
    print("\n" + "="*60)
    print("  Starting WebSocket Tests...")
    print("="*60)
    asyncio.run(test_websocket())
    
    # Summary
    print("\n" + "="*60)
    print("  ✅ ALL TESTS COMPLETED")
    print("="*60)
    print(f"⏰ Test Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n")

if __name__ == "__main__":
    main()
