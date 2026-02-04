import os
import sys
from unittest.mock import MagicMock, patch
from uuid import uuid4, UUID
from datetime import datetime, timezone

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.enums import ConversationMode, DecisionAction
from llm.schemas import PipelineResult, ClassifyOutput, RiskFlags

def test_static_followup_scheduling():
    print("Testing static followup scheduling...")
    
    # Mock api_client in both main and actions
    with patch('whatsapp_worker.main.api_client') as mock_api_main, \
         patch('whatsapp_worker.processors.actions.api_client') as mock_api_actions:
        
        from whatsapp_worker.main import process_message
        
        # Use mock_api_actions as the primary mock for assertions
        mock_api = mock_api_actions
        
        # Sync mock behavior
        mock_api_main.get_integration_with_org = mock_api.get_integration_with_org
        mock_api_main.get_or_create_lead = mock_api.get_or_create_lead
        mock_api_main.get_or_create_conversation = mock_api.get_or_create_conversation
        mock_api_main.get_conversation = mock_api.get_conversation
        mock_api_main.delete_pending_actions = mock_api.delete_pending_actions
        mock_api_main.store_incoming_message = mock_api.store_incoming_message
        
        # Setup mock data
        organization_id = uuid4()
        conversation_id = uuid4()
        lead_id = uuid4()
        
        mock_api.get_integration_with_org.return_value = {
            "organization_id": str(organization_id),
            "organization_name": "Test Org",
            "access_token": "test_token",
            "version": "v18.0",
        }
        mock_api.get_or_create_lead.return_value = {"id": str(lead_id), "phone": "1234567890"}
        mock_api.get_or_create_conversation.return_value = ({"id": str(conversation_id), "mode": "bot", "organization_id": str(organization_id)}, False)
        mock_api.get_conversation.return_value = {"id": str(conversation_id), "mode": "bot", "organization_id": str(organization_id)}
        mock_api.delete_pending_actions.return_value = 1
        
        # Mock dependencies in main
        with patch('whatsapp_worker.main.run_pipeline') as mock_pipeline, \
             patch('whatsapp_worker.main.build_pipeline_context') as mock_build_context, \
             patch('whatsapp_worker.main.handle_pipeline_result'), \
             patch('llm.steps.summarize.run_background_summary') as mock_summarize, \
             patch('whatsapp_worker.processors.context.api_client') as mock_ctx_api:
            
            mock_summarize.return_value = "New summary"
            mock_ctx_api.get_conversation_messages.return_value = []
            
            # Mock pipeline result
            mock_pipeline.return_value = PipelineResult(
                classification=ClassifyOutput(
                    thought_process="Thinking...",
                    situation_summary="Summary",
                    intent_level="unknown",
                    user_sentiment="neutral",
                    risk_flags=RiskFlags(),
                    action=DecisionAction.WAIT_SCHEDULE,
                    new_stage="greeting",
                    should_respond=False,
                    confidence=1.0
                ),
                response=None
            )
            mock_build_context.return_value = {}
            
            # Execute
            process_message("phone_id", "sender_phone", "sender_name", "Hello")
            
            # Verify deletion
            mock_api.delete_pending_actions.assert_called_with(conversation_id)
            print("✅ Existing actions deleted on lead message")
            
            # Verify 3 actions scheduled
            scheduled_calls = mock_api.create_scheduled_action.call_args_list
            assert len(scheduled_calls) == 3
            print("✅ 3 static followups scheduled")
            
            # Reset mocks for followup execution test
            mock_api.create_scheduled_action.reset_mock()
            mock_api.delete_pending_actions.reset_mock()
            
            # Simulate a followup execution (which calls handle_pipeline_result)
            from whatsapp_worker.processors.actions import handle_pipeline_result
            
            followup_result = PipelineResult(
                classification=ClassifyOutput(
                    thought_process="Following up...",
                    situation_summary="Nudge",
                    intent_level="unknown",
                    user_sentiment="neutral",
                    risk_flags=RiskFlags(),
                    action=DecisionAction.WAIT_SCHEDULE,
                    new_stage="greeting",
                    should_respond=False,
                    confidence=1.0
                ),
                response=None
            )
            
            handle_pipeline_result({"id": str(conversation_id), "organization_id": str(organization_id)}, lead_id, followup_result)
            
            # Verify NO new actions scheduled during followup (since static sequence is already in place)
            assert mock_api.create_scheduled_action.call_count == 0
            print("✅ No new actions scheduled during followup execution (PASSING)")
            
            # Verify NO deletion during followup execution
            assert mock_api.delete_pending_actions.call_count == 0
            print("✅ No actions deleted during followup execution (PASSING)")
            
            # Check intervals
            intervals = [10, 180, 360]
            for i, call in enumerate(scheduled_calls):
                args, kwargs = call
                assert kwargs['action_type'] == "followup"
                assert f"{intervals[i]}m" in kwargs['action_context']
            print("✅ Intervals (10m, 3h, 6h) are correct")

def test_safety_suppression():
    print("\nTesting safety suppression (Escalation & Stages)...")
    
    with patch('whatsapp_worker.main.api_client') as mock_api_main, \
         patch('whatsapp_worker.processors.actions.api_client') as mock_api_actions:
        
        from whatsapp_worker.main import process_message
        mock_api = mock_api_actions
        
        # Setup mock data for Escalation
        conversation_id = uuid4()
        organization_id = uuid4()
        lead_id = uuid4()
        
        mock_api_main.get_integration_with_org.return_value = {"organization_id": str(organization_id), "organization_name": "Test Org", "access_token": "token", "version": "v18.0"}
        mock_api_main.get_or_create_lead.return_value = {"id": str(lead_id), "phone": "1"}
        mock_api_main.get_or_create_conversation.return_value = ({"id": str(conversation_id), "mode": "bot", "organization_id": str(organization_id)}, False)
        mock_api_main.delete_pending_actions.return_value = 0
        
        # 1. Trigger Escalation
        mock_api_main.get_conversation.return_value = {
            "id": str(conversation_id), 
            "mode": "bot", 
            "organization_id": str(organization_id),
            "needs_human_attention": True  # ESCALATED
        }
        
        with patch('whatsapp_worker.main.run_pipeline') as mock_pipeline, \
             patch('whatsapp_worker.main.build_pipeline_context') as mock_build_context, \
             patch('whatsapp_worker.main.handle_pipeline_result'), \
             patch('llm.steps.summarize.run_background_summary'), \
             patch('whatsapp_worker.processors.context.api_client') as mock_ctx_api:
            
            mock_ctx_api.get_conversation_messages.return_value = []
            
            mock_pipeline.return_value = PipelineResult(
                classification=ClassifyOutput(thought_process="Escalate", situation_summary="", intent_level="unknown", user_sentiment="neutral", risk_flags=RiskFlags(), action=DecisionAction.FLAG_ATTENTION, new_stage="greeting", should_respond=False, confidence=1.0, needs_human_attention=True),
                response=None
            )
            # Context needs rolling_summary attribute for some paths
            mock_context = MagicMock()
            mock_context.rolling_summary = ""
            mock_build_context.return_value = mock_context
            
            # Execute
            process_message("id", "phone", "name", "Help")
            
            # Verify NO actions scheduled due to escalation
            assert mock_api.create_scheduled_action.call_count == 0
            print("✅ Followups suppressed for Escalated (human attention) conversations")

        # 2. Terminal Stage
        mock_api.create_scheduled_action.reset_mock()
        mock_api_main.get_conversation.return_value = {
            "id": str(conversation_id), 
            "mode": "bot", 
            "organization_id": str(organization_id),
            "stage": "closed"  # TERMINAL
        }
        
        process_message("id", "phone", "name", "Thanks")
        assert mock_api.create_scheduled_action.call_count == 0
        print("✅ Followups suppressed for Closed stage")


def test_race_condition_protection():
    print("\nTesting race condition protection in worker...")
    
    # Mock celery BEFORE importing tasks
    sys.modules['celery'] = MagicMock()
    import whatsapp_worker.tasks
    
    with patch('whatsapp_worker.tasks.api_client') as mock_api:
        from whatsapp_worker.tasks import process_single_followup
        
        conversation_id = uuid4()
        action_id = uuid4()
        
        # Case: User replied AFTER action was created
        # created_at: 21:00:00
        # last_user_message_at: 21:05:00
        action = {
            "id": str(action_id),
            "status": "pending",
            "created_at": "2026-02-04T21:00:00Z"
        }
        
        mock_api.get_followup_context.return_value = {
            "conversation": {
                "id": str(conversation_id),
                "mode": "bot",
                "last_user_message_at": "2026-02-04T21:05:00Z" # User replied LATER
            },
            "lead": {"id": str(uuid4()), "phone": "123"},
            "organization_id": str(uuid4()),
            "organization_name": "Test",
            "access_token": "token",
            "phone_number_id": "phone",
            "version": "v18.0"
        }
        
        # Execute
        process_single_followup(action)
        
        # Verify action deleted
        mock_api.delete_scheduled_action.assert_called_with(UUID(str(action_id)))
        print("✅ Race condition protected: Stale followup deleted when user replied since schedule")

if __name__ == "__main__":
    try:
        test_static_followup_scheduling()
        test_safety_suppression()
        test_race_condition_protection()
        print("\nALL TESTS PASSED")
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
