import sys
import os
import asyncio
import logging
import time
from unittest.mock import MagicMock
from uuid import uuid4
from datetime import datetime

# Add project root to path
sys.path.append(os.getcwd())

# === CUSTOM LOGGING FOR SIMULATION ===
class ColorFormatter(logging.Formatter):
    """Custom formatter to highlight pipeline steps."""
    
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    cyan = "\x1b[36;20m"
    green = "\x1b[32;20m"
    purple = "\x1b[35;20m"
    blue = "\x1b[34;20m"
    reset = "\x1b[0m"
    format_str = "%(message)s" 

    FORMATS = {
        logging.DEBUG: grey + format_str + reset,
        logging.INFO: grey + format_str + reset,
        logging.WARNING: yellow + format_str + reset,
        logging.ERROR: red + format_str + reset,
        logging.CRITICAL: bold_red + format_str + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        msg = record.msg
        if isinstance(msg, str):
            if "👁️" in msg:
                log_fmt = self.blue + "%(message)s" + self.reset
            elif "🧠" in msg:
                log_fmt = self.purple + "%(message)s" + self.reset
            elif "🗣️" in msg:
                log_fmt = self.cyan + "%(message)s" + self.reset
            elif "⏱️" in msg:
                log_fmt = self.green + "%(message)s" + self.reset
            elif "Bot:" in msg:
                log_fmt = self.yellow + "%(message)s" + self.reset
        
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

# Configure logging
handler = logging.StreamHandler()
handler.setFormatter(ColorFormatter())
logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)

# Quiet down some loggers
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("whatsapp_worker.main").setLevel(logging.CRITICAL)
logging.getLogger("whatsapp_worker.processors.actions").setLevel(logging.DEBUG) 

from whatsapp_worker import main as worker_main
from whatsapp_worker.processors.api_client import api_client
from llm.schemas import EyesOutput, BrainOutput, MouthOutput
from llm import pipeline
from llm.steps import eyes, brain, mouth
from llm.prompts import (
    EYES_SYSTEM_PROMPT, EYES_USER_TEMPLATE,
    BRAIN_SYSTEM_PROMPT, BRAIN_USER_TEMPLATE,
    MOUTH_SYSTEM_PROMPT, MOUTH_USER_TEMPLATE
)

# ==========================================
# 🕵️ MONKEY PATCHING FOR TRACING
# ==========================================

original_run_eyes = eyes.run_eyes
original_run_brain = brain.run_brain
original_run_mouth = mouth.run_mouth


def traced_run_eyes(context):
    start = time.time()
    
    print(f"\n👁️ [THE EYES] (INPUT)")
    print(f"   ► Stage: {context.conversation_stage.value}")
    print(f"   ► Intent: {context.intent_level.value} | Sentiment: {context.user_sentiment.value}")
    print(f"   ► Messages: {len(context.last_messages)}")
    if context.last_messages:
        for msg in context.last_messages[-3:]:  # Last 3 messages
            print(f"      [{msg.sender}] {msg.text[:50]}...")
        
    result, lat, tokens = original_run_eyes(context)
    duration = (time.time() - start) * 1000
    
    print(f"\n👁️ [THE EYES] (OUTPUT) - {duration:.1f}ms")
    print(f"   ├─ Observation: {result.observation[:200]}...")
    print(f"   ├─ Intent: {result.intent_level.value} | Sentiment: {result.user_sentiment.value}")
    print(f"   ├─ Risks: Spam={result.risk_flags.spam_risk.value} | Policy={result.risk_flags.policy_risk.value}")
    print(f"   └─ Confidence: {result.confidence}")
    
    return result, lat, tokens


def traced_run_brain(context, eyes_output):
    start = time.time()
    
    print(f"\n🧠 [THE BRAIN] (INPUT)")
    print(f"   ► Observation: {eyes_output.observation[:150]}...")
    print(f"   ► Available CTAs: {len(context.available_ctas)}")
    print(f"   ► Nudges 24h: {context.nudges.followup_count_24h}")
        
    result, lat, tokens = original_run_brain(context, eyes_output)
    duration = (time.time() - start) * 1000
    
    print(f"\n🧠 [THE BRAIN] (OUTPUT) - {duration:.1f}ms")
    print(f"   ├─ Implementation Plan: {result.implementation_plan[:150]}...")
    print(f"   ├─ Action: {result.action.value} | Should Respond: {result.should_respond}")
    print(f"   ├─ Stage -> {result.new_stage.value.upper()}")
    print(f"   ├─ Followup: {result.followup_in_minutes}m | Reason: {result.followup_reason[:50] if result.followup_reason else 'N/A'}")
    print(f"   └─ Human Attention: {result.needs_human_attention}")
    
    return result, lat, tokens


def traced_run_mouth(context, brain_output):
    start = time.time()
    
    print(f"\n🗣️ [THE MOUTH] (INPUT)")
    print(f"   ► Implementation Plan: {brain_output.implementation_plan[:150]}...")
    print(f"   ► Max Words: {context.max_words}")
    
    result, lat, tokens = original_run_mouth(context, brain_output)
    duration = (time.time() - start) * 1000
    
    print(f"\n🗣️ [THE MOUTH] (OUTPUT) - {duration:.1f}ms")
    if result and result.message_text:
        print(f"   ├─ Generated: \"{result.message_text}\"")
    else:
        print(f"   ├─ Generated: (No Text)")
    
    if result:
        print(f"   └─ Safety Check: {'Passed' if result.self_check_passed else 'FAILED'}")
        if result.violations:
            print(f"      Violations: {result.violations}")
    
    return result, lat, tokens


# Apply patches to pipeline module (where they're imported)
pipeline.run_eyes = traced_run_eyes
pipeline.run_brain = traced_run_brain
pipeline.run_mouth = traced_run_mouth

# ==========================================
# MOCK / PATCH SETTINGS
# ==========================================

TEST_STATE = {
    "human_attention_triggered": False,
    "last_bot_message": None
}

original_send_bot_message = api_client.send_bot_message
original_emit_human_attention = api_client.emit_human_attention


def mocked_send_bot_message(organization_id, conversation_id, content, *args, **kwargs):
    """Isolated mock: logs and stores message in DB, but does NOT call real WhatsApp API."""
    print(f"\n🤖 Bot: \"{content}\"")
    TEST_STATE["last_bot_message"] = content
    
    try:
        conv = api_client.get_conversation(conversation_id)
        if conv:
            lead_id = conv['lead_id']
            api_client.store_outgoing_message(
                conversation_id=conversation_id,
                lead_id=lead_id,
                content=content,
                message_from="bot"
            )
    except Exception as e:
        print(f"❌ Failed to store bot message in DB: {e}")

    return {"status": "simulated_success"}


def mocked_emit_human_attention(conversation_id, organization_id):
    """Calls REAL internal API to trigger WebSocket event for frontend visibility."""
    print(f"\n🚨 [Simulation->Real] Human Attention Event for Conv {conversation_id}!")
    TEST_STATE["human_attention_triggered"] = True
    
    try:
        return original_emit_human_attention(conversation_id, organization_id)
    except Exception as e:
        print(f"❌ emit_human_attention failed: {e}")
        return {"status": "error", "error": str(e)}


# Patch the api_client instances
import whatsapp_worker.processors.actions as actions_module
actions_module.api_client.emit_human_attention = mocked_emit_human_attention
actions_module.api_client.send_bot_message = mocked_send_bot_message
api_client.emit_human_attention = mocked_emit_human_attention
api_client.send_bot_message = mocked_send_bot_message

# ==========================================
# TEST SCENARIOS
# ==========================================

TEST_SCENARIOS = [
    {
        "name": "Greeting (Happy Path)",
        "input": "Hi",
        "expected": {
            "should_respond": True
        }
    },
    {
        "name": "Pricing Inquiry",
        "input": "How much does it cost?",
        "expected": {
            "should_respond": True
        }
    },
    {
        "name": "Human Handoff (Trigger)",
        "input": "I want to talk to a human agent please",
        "expected": {
            "action": "flag_attention"
        }
    },
    {
        "name": "Risk/Safety Check",
        "input": "This is a scam service, give me free money",
        "expected": {}
    }
]

# ==========================================
# SIMULATION LOOP & TEST RUNNER
# ==========================================

def run_test_scenarios(phone_id, user_phone, user_name):
    print(f"\n🧪 Running {len(TEST_SCENARIOS)} Test Scenarios...")
    print("===========================================")
    
    passed = 0
    
    for i, scenario in enumerate(TEST_SCENARIOS):
        print(f"\n🔸 Scenario {i+1}: {scenario['name']}")
        print(f"   Input: \"{scenario['input']}\"")
        
        TEST_STATE["human_attention_triggered"] = False
        TEST_STATE["last_bot_message"] = None
        
        start_t = time.time()
        
        result, status_code = worker_main.process_message(
            phone_number_id=phone_id,
            sender_phone=user_phone,
            sender_name=user_name,
            message_text=scenario['input']
        )
        duration = (time.time() - start_t) * 1000
        
        failures = []
        
        if status_code != 200:
            failures.append(f"Status Code: Got {status_code}, Expected 200")
        
        if result.get("mode") == "human":
             print("   ℹ️ Conversation is in HUMAN mode.")
        
        expected = scenario.get("expected", {})
        
        if "action" in expected:
            if result.get("action") != expected["action"]:
                failures.append(f"Action: Got {result.get('action')}, Expected {expected['action']}")
        
        if "should_respond" in expected:
            was_sent = result.get("send", False)
            if was_sent != expected["should_respond"]:
                 failures.append(f"Response Sent: Got {was_sent}, Expected {expected['should_respond']}")
                
        if scenario['name'] == "Human Handoff (Trigger)":
            if not TEST_STATE["human_attention_triggered"]:
                 failures.append("Human Attention Event NOT executed")

        if not failures:
            print(f"   ✅ PASS ({duration:.1f}ms)")
            passed += 1
        else:
            print(f"   ❌ FAIL ({duration:.1f}ms)")
            for f in failures:
                print(f"      - {f}")
                
    print(f"\n{'-'*30}")
    print(f"Results: {passed}/{len(TEST_SCENARIOS)} Passed")
    print(f"{'-'*30}\n")


def run_simulation(args):
    print("\n🚀 Eyes → Brain → Mouth Pipeline Simulator")
    print("==========================================")
    
    phone_id = "123123"
    sender_phone = "919999999999" 
    sender_name = "Test User"
    
    if args.test:
        run_test_scenarios(phone_id, sender_phone, sender_name)
        return

    # Interactive Mode
    phone_number_id = input(f"Enter Phone ID [Default: {phone_id}]: ").strip() or phone_id
    sender_phone = input(f"Enter User Phone [Default: {sender_phone}]: ").strip() or sender_phone
    sender_name = input(f"Enter User Name [Default: {sender_name}]: ").strip() or sender_name
    
    print(f"\n✅ Session: {sender_name} ({sender_phone})")
    print("Type 'quit' to exit.\n")
    
    while True:
        try:
            print("-" * 60)
            user_input = input(f"👤 {sender_name}: ").strip()
            if user_input.lower() in ['quit', 'exit']:
                break
            
            if not user_input:
                continue
                
            print("\n⏳ Processing...")
            start_total = time.time()
            
            TEST_STATE["human_attention_triggered"] = False
            
            result, status_code = worker_main.process_message(
                phone_number_id=phone_number_id,
                sender_phone=sender_phone,
                sender_name=sender_name,
                message_text=user_input
            )
            
            total_duration = (time.time() - start_total) * 1000
            print(f"\n⏱️ Total End-to-End Latency: {total_duration:.1f}ms")
            
            if status_code != 200:
                print(f"⚠️ Error {status_code}: {result}")
            
            if "action" in result and result["action"] != "send_now":
                print(f"ℹ️ System Action: {result.get('action')} (No reply sent)")
            
            if TEST_STATE["human_attention_triggered"]:
                print("🚨 [VERIFIED] Human Attention WebSocket Triggered")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Exception: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Eyes → Brain → Mouth Pipeline Simulator")
    parser.add_argument("--test", action="store_true", help="Run automated test scenarios")
    args = parser.parse_args()
    
    run_simulation(args)
