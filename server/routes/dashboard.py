from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from server.dependencies import get_db
from server.dependencies import get_auth_context
from server.schemas import DashboardStatsOut, AuthContext
from server.models import Conversation, Message, Lead

router = APIRouter()

@router.get("/stats", response_model=DashboardStatsOut)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context)
):
    # This is a sample implementation. In a real app, you'd aggregate these from the DB.
    total_conversations = db.query(Conversation).filter(Conversation.organization_id == auth.organization_id).count()
    total_messages = db.query(Message).filter(Message.organization_id == auth.organization_id).count()
    active_leads = db.query(Lead).filter(Lead.organization_id == auth.organization_id).count()
    
    # Empty metrics instead of mock data
    peak_hours = {}
    sentiment_breakdown = {}
    
    return DashboardStatsOut(
        total_conversations=total_conversations,
        total_messages=total_messages,
        active_leads=active_leads,
        peak_hours=peak_hours,
        sentiment_breakdown=sentiment_breakdown
    )
