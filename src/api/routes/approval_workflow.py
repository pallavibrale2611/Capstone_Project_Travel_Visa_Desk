"""
Approval workflow API routes
"""

from fastapi import APIRouter, HTTPException
from src.api.models.approval_models import ApprovalRequest, ApprovalResponse
from src.services.approval_service import ApprovalService
from src.utils.logger import get_logger
import sqlite3
import json
from datetime import datetime, timezone


router = APIRouter(prefix="/api/approvals", tags=["Approval Workflow"])
approval_service = ApprovalService()
logger = get_logger(__name__)

# --- Workflow Definition ---
# Defines the stages of the visa application process in order.
# WORKFLOW_STAGES = [
#     "hr_team",
#     "legal_team",
#     "management_team"
# ]

# def get_next_stage(current_stage: str) -> str | None:
#     """
#     Determines the next stage in the workflow.
#     """
#     try:
#         current_index = WORKFLOW_STAGES.index(current_stage)
#         if current_index + 1 < len(WORKFLOW_STAGES):
#             return WORKFLOW_STAGES[current_index + 1]
#         else:
#             # This is the last stage
#             return None
#     except ValueError:
#         # If the current stage is not in the workflow, return the first stage.
#         return WORKFLOW_STAGES[0]
    
# @router.post("/process", response_model=ApprovalResponse)
# async def process_approval_request(request: ApprovalRequest):
#     """
#     Process approval/rejection/change request.
#     Consolidated endpoint that handles:
#     - Approval validation
#     - Workflow progression
#     - Status updates
#     - Notifications
#     """
#     try:
#         logger.info(f"Processing approval for application {request.application_id}")
        
#         # In production:
#         # 1. Retrieve application and stages
#         # 2. Validate approver permissions
#         # 3. Process approval
#         # 4. Update database
#         # 5. Send notifications
#         conn = sqlite3.connect("visa_applications.db")
#         cursor = conn.cursor()

#         # Retrieve the current application data, including the status
#         cursor.execute('SELECT application_data, approval_status  FROM visa_applications WHERE id = ?', (request.application_id,))
#         result = cursor.fetchone()

#         if not result:
#             conn.close()
#             raise HTTPException(status_code=404, detail=f"Application {request.application_id} not found")

#         application_data_str, current_status = result
       

#         if request.action == "approve":
#             next_stage = get_next_stage(current_status)

#             if next_stage:
#                 # --- Update the application status in the database ---
#                 app_data = json.loads(application_data_str)

#                 # --- 2. Create the new history entry ---
#                 history_entry = {
#                     "approver": request.approver_id,
#                     "role":  request.approver_role ,  # You might want to get this from the user's profile
#                     "action": request.action,
#                     "timestamp": datetime.now(timezone.utc).isoformat(),
#                     "comments": request.comments
#                 }
                
#                 # --- 3. Update the application data dictionary ---
#                 if "approval_history" not in app_data:
#                     app_data["approval_history"] = []
#                 app_data["approval_history"].append(history_entry)
                
#                 app_data["current_stage"] = next_stage
#                 app_data["updated_at"] = datetime.now(timezone.utc).isoformat()
                
#                 # NOTE: Implement your logic to determine the next approver
#                 app_data["current_approver"] = next_stage

#                 # --- 4. Convert back to JSON and update the database ---
#                 updated_application_data = json.dumps(app_data)
                
#                 # Update both the detailed JSON and the high-level status column
#                 cursor.execute(
#                     'UPDATE visa_applications SET application_data = ?, status = ? WHERE id = ?',
#                     (updated_application_data, next_stage, request.application_id)
#                 )
#                 conn.commit()
#                 conn.close()

#                 logger.info(f"Application {request.application_id} approved and moved to {next_stage}")

#                 return ApprovalResponse(
#                     success=True,
#                     message=f"Application approved and moved to {next_stage}",
#                     application_status=next_stage
#                 )
#             else:
#                 # --- This is the final stage of the workflow ---
#                 final_status = "Workflow Completed"
#                 cursor.execute('UPDATE visa_applications SET status = ? WHERE id = ?', (final_status, request.application_id))
#                 conn.commit()
#                 conn.close()

#                 logger.info(f"Application {request.application_id} has completed the workflow.")

#                 return ApprovalResponse(
#                     success=True,
#                     message="Workflow completed successfully",
#                     application_status=final_status
#                 )
#         elif request.action in ["reject", "request_change"]:
#             # --- Handle rejections or requests for changes ---
#             new_status = "Rejected" if request.action == "reject" else "Changes Requested"
#             cursor.execute('UPDATE visa_applications SET status = ? WHERE id = ?', (new_status, request.application_id))
#             conn.commit()
#             conn.close()

#             logger.info(f"Application {request.application_id} has been {new_status.lower()}.")
#             # You could also store request.comments in the database.

#             return ApprovalResponse(
#                 success=True,
#                 message=f"Application has been {new_status.lower()}",
#                 application_status=new_status
#             )
#         else:
#             conn.close()
#             raise HTTPException(status_code=400, detail="Invalid action specified.")
    
#     except ValueError as e:
#         raise HTTPException(status_code=400, detail=str(e))
#     except Exception as e:
#         logger.error(f"Error processing approval: {str(e)}")
#         raise HTTPException(status_code=500, detail="Failed to process approval")
#     return None

WORKFLOW_STAGES = ["hr_team", "legal_team", "management_team"]

def get_next_stage(current_stage: str) -> str | None:
    """
    Determines the next stage in the workflow.
    """
    try:
        idx = WORKFLOW_STAGES.index(current_stage)
        return WORKFLOW_STAGES[idx + 1] if idx + 1 < len(WORKFLOW_STAGES) else None
    except ValueError:
        return WORKFLOW_STAGES[0]  # Default to first stage if invalid


@router.post("/process", response_model=ApprovalResponse)
async def process_approval_request(request: ApprovalRequest):
    """
    Handles approval/rejection/change requests:
    - Updates visa_applications table
    - Inserts into approval_history
    """
    try:
        logger.info(f"Processing approval for application {request.application_id}")
        conn = sqlite3.connect("visa_applications.db")
        cursor = conn.cursor()

        # Fetch current stage and status
        cursor.execute("""
                SELECT va.current_stage, va.status, td.destination_country
                FROM visa_applications va
                JOIN travel_details td ON va.id = td.application_id
                WHERE va.id = ?
            """,
            (request.application_id,)
        )
        result = cursor.fetchone()
        if not result:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Application {request.application_id} not found")

        current_stage, current_status ,embassy = result
        timestamp = datetime.now(timezone.utc).isoformat()

        # Validate approver role
        if current_stage != request.approver_role:
            conn.close()
            raise HTTPException(status_code=403, detail="Approver role does not match current stage")

        # Insert approval history record
        cursor.execute("""
            INSERT INTO approval_history (application_id, approver, role, action, timestamp, comments)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            request.application_id,
            request.approver_id,
            request.approver_role,
            request.action,
            timestamp,
            request.comments
        ))

        if request.action == "approve":
            next_stage = get_next_stage(current_stage)
            if next_stage:
                # Move to next stage
                cursor.execute("""
                    UPDATE visa_applications
                    SET current_stage = ?, current_approver = ?, approval_status = ?, updated_at = ?
                    WHERE id = ?
                """, (
                    next_stage,
                    next_stage,  # You can replace with actual approver logic
                    "pending",
                    timestamp,
                    request.application_id
                ))
                conn.commit()
                conn.close()
                return ApprovalResponse(
                    success=True,
                    message=f"Application approved and moved to {next_stage}",
                    application_status=f"Pending with {next_stage}"
                )
            else:
                # Final stage completed
                cursor.execute("""
                    UPDATE visa_applications
                    SET current_stage = ?, status = ?, approval_status = ?, updated_at = ?
                    WHERE id = ?
                """, (
                    "completed",
                    "Workflow Completed",
                    "approved",
                    timestamp,
                    request.application_id
                ))

                cursor.execute('''
                    INSERT INTO embassy_tracking (
                        application_id, status, embassy_name, tracking_number,
                        submission_date, last_updated, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    request.application_id,
                    "pending",
                    embassy,
                    'tracking_number',
                    timestamp,
                    timestamp,
                    "We Will update you once the embassy processes the application."
                ))


                conn.commit()
                conn.close()
                return ApprovalResponse(
                    success=True,
                    message="Workflow completed successfully",
                    application_status="Workflow Completed"
                )

        elif request.action in ["reject", "request_change"]:
            new_status = "Rejected" if request.action == "reject" else "Changes Requested"
            cursor.execute("""
                UPDATE visa_applications
                SET status = ?, approval_status = ?, updated_at = ?
                WHERE id = ?
            """, (
                new_status,
                "rejected" if request.action == "reject" else "pending",
                timestamp,
                request.application_id
            ))
            conn.commit()
            conn.close()
            return ApprovalResponse(
                success=True,
                message=f"Application has been {new_status.lower()}",
                application_status=new_status
            )

        else:
            conn.close()
            raise HTTPException(status_code=400, detail="Invalid action specified.")

    except Exception as e:
        logger.error(f"Error processing approval: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process approval {str(e)}")

@router.get("/applications/{application_id}/approval-status")
async def get_approval_status(application_id: str):
    """Get detailed approval status and history."""
    try:
        # In production:
        #status = approval_service.get_approval_status(application, stages)
        
        return {
            "application_id": application_id,
            "current_status": "hr_review",
            "stages": [],
            "history": []
        }
    
    except Exception as e:
        logger.error(f"Error fetching approval status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch approval status")


@router.get("/pending")
async def get_pending_approvals(approver_role: str):
    """Get all applications pending approval based on role. allowed roles: hr_team , legal_team ,management_team"""
    try:
        logger.info(f"Fetching pending approvals for {approver_role}")

        try:
            conn = sqlite3.connect("visa_applications.db")
            cursor = conn.cursor()
           
            cursor.execute('SELECT id from visa_applications WHERE current_stage = ? ', (approver_role,))
            #
            result = cursor.fetchone()
            conn.close()
           
            if result:
                print("Found pending applications ",result)
                app_data = [i for i in result]
                return app_data

            else:
                logger.warning(f"Applications not found")
                return None
               
        except Exception as e:
            logger.error(f"Failed to retrieve applications : {e}")
            return None


        
        # # In production: Query database for pending approvals
        # return {
        #     "approver_role": approver_role,
        #     "pending_count": 0,
        #     "applications": []
        # }
    
    except Exception as e:
        logger.error(f"Error fetching pending approvals: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch pending approvals")
