"""
Approval workflow service
Manages multi-level approval process
"""

from typing import List, Dict, Any, Optional
from src.api.models.visa_models import VisaApplication, ApplicationStatus
from src.api.models.approval_models import (
    ApprovalStage, ApprovalRequest, ApprovalResponse,
    ApprovalAction, ApproverRole
)
from datetime import datetime
import yaml

class ApprovalService:
    def __init__(self):
        """Initialize approval service with workflow configuration."""
        with open("config/visa_requirements.yaml", 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.workflows = self.config['approval_workflow']
    
    def start_workflow(
        self,
        application: VisaApplication
    ) -> List[ApprovalStage]:
        """
        Initialize approval workflow for application.
        
        Args:
            application: Visa application
        
        Returns:
            List of approval stages
        """
        visa_type = application.visa_type.value
        workflow_config = self.workflows.get(visa_type, self.workflows['business'])
        
        stages = []
        for stage_config in workflow_config:
            stage = ApprovalStage(
                stage=stage_config['stage'],
                approver_role=ApproverRole(stage_config['approver_role']),
                required=stage_config['required'],
                status="pending"
            )
            stages.append(stage)
        
        # Set first stage as current
        if stages:
            application.status = self._stage_to_status(stages[0].stage)
            application.current_approver = stages[0].approver_role.value
        
        return stages
    
    def process_approval(
        self,
        request: ApprovalRequest,
        application: VisaApplication,
        stages: List[ApprovalStage]
    ) -> ApprovalResponse:
        """
        Process approval/rejection request.
        
        Args:
            request: Approval request
            application: Visa application
            stages: Current approval stages
        
        Returns:
            Approval response with next steps
        """
        # Find current stage
        current_stage_idx = None
        for idx, stage in enumerate(stages):
            if stage.status == "pending":
                current_stage_idx = idx
                break
        
        if current_stage_idx is None:
            return ApprovalResponse(
                success=False,
                message="No pending approval stage found",
                application_status=application.status.value
            )
        
        current_stage = stages[current_stage_idx]
        
        # Validate approver role
        if current_stage.approver_role != request.approver_role:
            return ApprovalResponse(
                success=False,
                message=f"Invalid approver role. Expected {current_stage.approver_role.value}",
                application_status=application.status.value
            )
        
        # Process action
        current_stage.approver_id = request.approver_id
        current_stage.action_date = datetime.now()
        current_stage.comments = request.comments
        
        if request.action == ApprovalAction.APPROVE:
            current_stage.status = "approved"
            
            # Add to approval history
            application.approval_history.append({
                "stage": current_stage.stage,
                "approver_id": request.approver_id,
                "approver_role": request.approver_role.value,
                "action": "approved",
                "timestamp": datetime.now().isoformat(),
                "comments": request.comments
            })
            
            # Move to next stage or complete
            if current_stage_idx < len(stages) - 1:
                next_stage = stages[current_stage_idx + 1]
                application.status = self._stage_to_status(next_stage.stage)
                application.current_approver = next_stage.approver_role.value
                
                return ApprovalResponse(
                    success=True,
                    message=f"Approved. Moving to {next_stage.stage}",
                    next_stage=next_stage.stage,
                    next_approver_role=next_stage.approver_role,
                    application_status=application.status.value
                )
            else:
                application.status = ApplicationStatus.APPROVED
                application.current_approver = None
                
                return ApprovalResponse(
                    success=True,
                    message="Application fully approved",
                    application_status=application.status.value
                )
        
        elif request.action == ApprovalAction.REJECT:
            current_stage.status = "rejected"
            application.status = ApplicationStatus.REJECTED
            
            application.approval_history.append({
                "stage": current_stage.stage,
                "approver_id": request.approver_id,
                "approver_role": request.approver_role.value,
                "action": "rejected",
                "timestamp": datetime.now().isoformat(),
                "comments": request.comments
            })
            
            return ApprovalResponse(
                success=True,
                message="Application rejected",
                application_status=application.status.value
            )
        
        else:  # REQUEST_CHANGES
            application.status = ApplicationStatus.DRAFT
            
            application.approval_history.append({
                "stage": current_stage.stage,
                "approver_id": request.approver_id,
                "approver_role": request.approver_role.value,
                "action": "requested_changes",
                "timestamp": datetime.now().isoformat(),
                "comments": request.comments
            })
            
            return ApprovalResponse(
                success=True,
                message="Changes requested. Application returned to draft",
                application_status=application.status.value
            )
    
    def get_approval_status(
        self,
        application: VisaApplication,
        stages: List[ApprovalStage]
    ) -> Dict[str, Any]:
        """Get current approval status and history."""
        return {
            "current_status": application.status.value,
            "current_approver": application.current_approver,
            "stages": [
                {
                    "stage": stage.stage,
                    "approver_role": stage.approver_role.value,
                    "status": stage.status,
                    "action_date": stage.action_date.isoformat() if stage.action_date else None,
                    "comments": stage.comments
                }
                for stage in stages
            ],
            "history": application.approval_history
        }
    
    def _stage_to_status(self, stage: str) -> ApplicationStatus:
        """Convert stage name to application status."""
        stage_map = {
            "hr_review": ApplicationStatus.HR_REVIEW,
            "legal_review": ApplicationStatus.LEGAL_REVIEW,
            "management_approval": ApplicationStatus.MANAGEMENT_APPROVAL,
            "ceo_approval": ApplicationStatus.MANAGEMENT_APPROVAL
        }
        return stage_map.get(stage, ApplicationStatus.SUBMITTED)
    