"""
Approval workflow models
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

class ApprovalAction(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_CHANGES = "request_changes"

class ApproverRole(str, Enum):
    HR_MANAGER = "hr_team"
    LEGAL_COUNSEL = "legal_team"
    DEPARTMENT_HEAD = "management_team"
    CEO = "ceo"

class ApprovalStage(BaseModel):
    stage: str
    approver_role: ApproverRole
    approver_id: Optional[str] = None
    required: bool = True
    status: str = "pending"  # pending, approved, rejected
    action_date: Optional[datetime] = None
    comments: Optional[str] = None

class ApprovalRequest(BaseModel):
    application_id: str
    approver_id: str
    approver_role: ApproverRole
    action: ApprovalAction
    comments: Optional[str] = None

class ApprovalResponse(BaseModel):
    success: bool
    message: str
    next_stage: Optional[str] = None
    next_approver_role: Optional[ApproverRole] = None
    application_status: str