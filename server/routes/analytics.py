from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from server.dependencies import get_db
from server.dependencies import get_auth_context
from server.models import Analytics as AnalyticsModel
from server.schemas import AnalyticsOut, AuthContext
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/", response_model=List[AnalyticsOut])
def get_analytics(
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context)
):
    # Fetch analytics records for the organization
    # For now, if no records exist, we might return some mock data or an empty list
    analytics_records = db.query(AnalyticsModel).filter(
        AnalyticsModel.organization_id == auth.organization_id
    ).order_by(AnalyticsModel.metric_date.desc()).all()
    
    return analytics_records
