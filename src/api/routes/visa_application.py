from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
import logging
from src.api.models.visa_models import Document
 
from src.api.models.visa_models import (
    VisaApplication,
    CreateApplicationRequest,
    CreateApplicationResponse,
    DocumentValidationResult,
    ApplicationStatusResponse,
    ApplicationStatus,
    VisaApplicationPatch
)
from src.services.visa_service import VisaService
 
router = APIRouter(prefix="/api/visa", tags=["Visa Applications"])
logger = logging.getLogger(__name__)
 
# Dependency to get visa service
def get_visa_service() -> VisaService:
    return VisaService()
 

@router.post(
    "/applications",
    response_model=CreateApplicationResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_visa_application(
    request: CreateApplicationRequest,
    visa_service: VisaService = Depends(get_visa_service)
):
    """
    Create a new visa application.
   
    Args:
        request: CreateApplicationRequest with applicant, visa_type, travel_details
   
    Returns:
        CreateApplicationResponse with created application
    """
    try:
        logger.info(f"Creating visa application for {request.applicant.email}")
       
        # Create application
        response = visa_service.create_application(request)
       
        logger.info(f"Application {response.application_id} created successfully")
        return response
       
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating application: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create application: {str(e)}"
        )
 
@router.get(
    "/applications/{application_id}",
    response_model=VisaApplication
)
async def get_visa_application(
    application_id: str,
    visa_service: VisaService = Depends(get_visa_service)
):
    """
    Get visa application by ID.
   
    Args:
        application_id: Application ID
   
    Returns:
        VisaApplication object
    """
    try:
        application = visa_service.get_application(application_id)
       
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application {application_id} not found"
            )
       
        return application
       
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving application: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve application: {str(e)}"
        )
 
@router.put(
    "/applications/{application_id}",
    response_model=VisaApplication
)
async def update_visa_application(
    application_id: str,
    application: VisaApplication,
    visa_service: VisaService = Depends(get_visa_service)
):
    """
    Update existing visa application.
   
    Args:
        application_id: Application ID
        application: Updated application data
   
    Returns:
        Updated VisaApplication
    """
    try:
        # Ensure ID matches
        application.id = application_id
       
        success = visa_service.update_application(application)
       
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application {application_id} not found"
            )
       
        # Return updated application
        updated = visa_service.get_application(application_id)
        return updated
       
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating application: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update application: {str(e)}"
        )
 
@router.post(
    "/applications/{application_id}/submit",
    response_model=VisaApplication
)
async def submit_visa_application(
    application_id: str,
    visa_service: VisaService = Depends(get_visa_service)
):
    """
    Submit visa application for approval.
   
    Args:
        application_id: Application ID
   
    Returns:
        Updated VisaApplication with submitted status
    """
    try:
        application = visa_service.submit_application(application_id)
       
        logger.info(f"Application {application_id} submitted successfully")
        return application
       
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error submitting application: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit application: {str(e)}"
        )
 
@router.get(
    "/applications/{application_id}/status",
    response_model=ApplicationStatusResponse
)
async def get_application_status(
    application_id: str,
    visa_service: VisaService = Depends(get_visa_service)
):
    """
    Get application status and tracking information.
   
    Args:
        application_id: Application ID
   
    Returns:
        ApplicationStatusResponse with status details
    """
    try:
        status_info = visa_service.track_application_status(application_id)
        return status_info
       
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error tracking application status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to track application: {str(e)}"
        )
 
@router.post(
    "/applications/{application_id}/validate-documents",
    response_model=DocumentValidationResult
)
async def validate_application_documents(
    application_id: str,
    visa_service: VisaService = Depends(get_visa_service)
):
    """
    Validate documents for an application.
   
    Args:
        application_id: Application ID
   
    Returns:
        DocumentValidationResult with validation details
    """
    try:
        application = visa_service.get_application(application_id)
       
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application {application_id} not found"
            )
       
        validation_result = visa_service.validate_documents(application)
        return validation_result
       
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate documents: {str(e)}"
        )
 
@router.get(
    "/applications/employee/{employee_id}",
    response_model=List[VisaApplication]
)
async def get_employee_applications(
    employee_id: str,
    visa_service: VisaService = Depends(get_visa_service)
):
    """
    Get all applications for an employee.
   
    Args:
        employee_id: Employee ID
   
    Returns:
        List of VisaApplication objects
    """
    try:
        applications = visa_service.get_applications_by_employee(employee_id)
        return applications
       
    except Exception as e:
        logger.error(f"Error retrieving employee applications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve applications: {str(e)}"
        )
 
@router.get(
    "/applications/status/{status}",
    response_model=List[VisaApplication]
)
async def get_applications_by_status(
    status: ApplicationStatus,
    visa_service: VisaService = Depends(get_visa_service)
):
    """
    Get all applications with specific status.
   
    Args:
        status: ApplicationStatus enum value
   
    Returns:
        List of VisaApplication objects
    """
    try:
        applications = visa_service.get_applications_by_status(status)
        return applications
       
    except Exception as e:
        logger.error(f"Error retrieving applications by status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve applications: {str(e)}"
        )
 
@router.delete(
    "/applications/{application_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_visa_application(
    application_id: str,
    visa_service: VisaService = Depends(get_visa_service)
):
    """
    Delete visa application (only draft applications).
   
    Args:
        application_id: Application ID
    """
    try:
        application = visa_service.get_application(application_id)
       
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application {application_id} not found"
            )
       
        # Only allow deletion of draft applications
        if application.status != ApplicationStatus.DRAFT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only draft applications can be deleted"
            )
       
        # Implement deletion in service
        # visa_service.delete_application(application_id)
       
        logger.info(f"Application {application_id} deleted")
       
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting application: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete application: {str(e)}"
        )
 
@router.patch("/applications/{application_id}",
               response_model=VisaApplication
               )
async def patch_visa_application(
    application_id: str,
    application_data: VisaApplicationPatch,  # Accept partial data
    visa_service: VisaService = Depends(get_visa_service)
):
    """
    Partially update an existing visa application.
    """
    try:
        success = visa_service.patch_application(application_id, application_data.model_dump(exclude_unset=True))
        if not success:
            raise HTTPException(status_code=404, detail=f"Application {application_id} not found")

        return visa_service.get_application(application_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error patching application: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to patch application: {str(e)}")
    
@router.put("/applications/{application_id}/embassy")
async def update_embassy_tracking(
    application_id: str,
    request: dict,
    visa_service: VisaService = Depends(get_visa_service)
):
    """
    Update embassy tracking status - simple version.
    """
    try:
        logger.info(f"Updating embassy tracking for {application_id} with data: {request}")
       
        success = visa_service.update_embassy_status(application_id, request)
       
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update embassy status"
            )
       
        # Get updated status to return
        embassy_status = visa_service.get_embassy_status(application_id)
       
        return {
            "success": True,
            "message": f"Embassy status updated to {request.get('status')}",
            "application_id": application_id,
            "embassy_status": embassy_status
        }
       
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating embassy status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update embassy status: {str(e)}"
        )
    
    
@router.get("/applications/{application_id}/embassy")
async def get_embassy_tracking(
    application_id: str,
    visa_service: VisaService = Depends(get_visa_service)
):
    """
    get embassy tracking status - simple version.
    """
    try:
        logger.info(f"Getting embassy tracking for {application_id} ")
       
        success = visa_service.get_embassy_status(application_id)
        print(success,"embassy status success")
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update embassy status"
            )
        
        return success
       
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting embassy status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get embassy status: {str(e)}"
        )    
    
#src/routes/visa_application.py
@router.post(
    "/applications/{application_id}/validate-documents-content",
    response_model=DocumentValidationResult,  # Use existing DocumentValidationResult model
    summary="Validate Document Content",
    description="Validate if documents have content and are properly filled"
)
async def validate_document_content(
    application_id: str,
    visa_service: VisaService = Depends(get_visa_service)
):
    """
    Validate if documents have content and are properly filled.
   
    Args:
        application_id: Application ID
       
    Returns:
        DocumentValidationResult with validation details
    """
    try:
        # Get the application
        application = visa_service.get_application(application_id)
       
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application {application_id} not found"
            )
       
        # Validate document content using service method that checks documents table
        validation_result = visa_service.validate_document_content_enhanced(application_id)
        return validation_result
       
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating document content: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate document content: {str(e)}"
        )

@router.post(
    "/applications/{application_id}/upload-documents",
    response_model=Document
)
async def upload_documents(
    application_id: str,
    document: Document,
    visa_service: VisaService = Depends(get_visa_service)
):
    """
    Upload documents for a visa application.
   
    Args:
        application_id: Application ID
        document: Document object containing file details"""
    try:
        logger.info(f"Uploading document for application {application_id}")
       
        # Upload document using service method
        response = visa_service.upload_document(application_id, document)
       
        logger.info(f"Document uploaded successfully for application {application_id}")
        return response
       
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}"
        )
    return response
