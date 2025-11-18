# """
# Pydantic models for visa application
# """

# from pydantic import BaseModel, Field, field_validator
# from typing import List, Optional, Dict, Any
# from datetime import datetime, date
# from enum import Enum

# class VisaType(str, Enum):
#     BUSINESS = "business"
#     TOURIST = "tourist"
#     WORK = "work"
#     STUDENT = "student"
#     TRANSIT = "transit"
#     DIPLOMATIC = "diplomatic"

# class ApplicationStatus(str, Enum):
#     DRAFT = "draft"
#     SUBMITTED = "submitted"
#     HR_REVIEW = "hr_review"
#     LEGAL_REVIEW = "legal_review"
#     MANAGEMENT_APPROVAL = "management_approval"
#     APPROVED = "approved"
#     REJECTED = "rejected"
#     EMBASSY_SUBMITTED = "embassy_submitted"
#     EMBASSY_PROCESSING = "embassy_processing"
#     VISA_ISSUED = "visa_issued"

# class DocumentType(str, Enum):
#     PASSPORT = "passport"
#     PASSPORT_PHOTO = "passport_photos"
#     EMPLOYMENT_LETTER = "employment_letter"
#     BANK_STATEMENT = "bank_statements"
#     INVITATION_LETTER = "invitation_letter"
#     FLIGHT_ITINERARY = "flight_itinerary"
#     HOTEL_RESERVATION = "hotel_reservation"
#     TRAVEL_INSURANCE = "travel_insurance"

# class Document(BaseModel):
#     id: Optional[str] = None
#     type: DocumentType
#     filename: str
#     file_path: str
#     uploaded_at: datetime = Field(default_factory=datetime.now)
#     validated: bool = False
#     validation_notes: Optional[str] = None
#     version: int = 1

# class ApplicantInfo(BaseModel):
#     employee_id: str
#     first_name: str
#     last_name: str
#     email: str
#     department: str
#     position: str
#     nationality: str
#     passport_number: str
#     passport_expiry: date
#     date_of_birth: date
    
#     @field_validator('passport_expiry')
#     def validate_passport_expiry(cls, v):
#         if v < datetime.now().date():
#             raise ValueError('Passport has expired')
#         return v

# class TravelDetails(BaseModel):
#     destination_country: str
#     purpose_of_travel: str
#     departure_date: date
#     return_date: date
#     duration_days: int
#     cities_to_visit: List[str]
    
#     @field_validator('return_date')
#     def validate_dates(cls, v, values):
#         dd = values.data.get('departure_date')
#         if dd  and v < dd :
#             raise ValueError('Return date must be after departure date')
#         return v

# class VisaApplication(BaseModel):
#     id: Optional[str] = None
#     applicant: ApplicantInfo
#     visa_type: VisaType
#     travel_details: TravelDetails
#     documents: List[Document] = []
#     status: ApplicationStatus = ApplicationStatus.DRAFT
#     created_at: datetime = Field(default_factory=datetime.now)
#     updated_at: datetime = Field(default_factory=datetime.now)
#     submitted_at: Optional[datetime] = None
#     current_approver: Optional[str] = None
#     approval_history: List[Dict[str, Any]] = []
#     notes: Optional[str] = None
#     session_id: Optional[str] = None

# class VisaRequirement(BaseModel):
#     country: str
#     visa_type: VisaType
#     required_documents: List[str]
#     processing_time_days: int
#     validity_months: int
#     fees: Dict[str, float]
#     special_requirements: List[str] = []
#     embassy_contacts: Dict[str, str] = {}

# class DocumentValidationRequest(BaseModel):
#     application_id: str
#     document_id: str

# class DocumentValidationResponse(BaseModel):
#     valid: bool
#     issues: List[str] = []
#     suggestions: List[str] = []

"""
Visa Application Models
src/api/models/visa_models.py
"""
 
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from enum import Enum
 
# ============================================================================
# ENUMS
# ============================================================================

class ApplicantTool(BaseModel):
    employee_id: str = Field(description="The employee's unique ID")
    first_name: str = Field(description="The applicant's first name")
    last_name: str = Field(description="The applicant's last name")
    email: str = Field(description="The applicant's email address")
    department: str = Field(description="The applicant's department")
    position: str = Field(description="The applicant's job position")
    nationality: str = Field(description="The applicant's nationality")
    passport_number: str = Field(description="The applicant's passport number")
    passport_expiry: str = Field(description="The passport's expiry date in YYYY-MM-DD format")
    date_of_birth: str = Field(description="The applicant's date of birth in YYYY-MM-DD format")

class TravelDetailsTool(BaseModel):
    destination_country: str = Field(description="The country the applicant is traveling to")
    purpose_of_travel: str = Field(description="The reason for the travel")
    departure_date: str = Field(description="The date of departure in YYYY-MM-DD format")
    return_date: str = Field(description="The date of return in YYYY-MM-DD format")
    duration_days: int = Field(description="The total duration of the trip in days")
    cities_to_visit: List[str] = Field(description="A list of cities to be visited")

class CreateApplicationArgsTool(BaseModel):
    """Input schema for the Create_Visa_Application tool."""
    applicant: ApplicantTool = Field(description="The applicant's personal and professional details")
    visa_type: str = Field(description="The type of visa being applied for (e.g., 'work', 'tourist')")
    travel_details: TravelDetailsTool = Field(description="Details about the planned travel itinerary")
    notes: Optional[str] = Field(description="Any additional notes for the application", default=None)


class ApplicationStatus(str, Enum):
    """Application status enum."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    WORKFLOW  = "Workflow Completed"
class DocumentType(str, Enum):
    """Document types."""
    PASSPORT = "passport"
    PASSPORT_PHOTOS = "passport_photos"
    EMPLOYMENT_LETTER = "employment_letter"
    INVITATION_LETTER = "invitation_letter"
    BANK_STATEMENT = "bank_statement"
    FLIGHT_ITINERARY = "flight_itinerary"
    HOTEL_BOOKING = "hotel_booking"
    EMPLOYMENT_CONTRACT = "employment_contract"
    QUALIFICATION_CERTIFICATES = "qualification_certificates"
    OTHER = "other"
 
# ============================================================================
# CORE MODELS
# ============================================================================
 
class Applicant(BaseModel):
    """Applicant information model."""
    employee_id: str = Field(..., description="Employee ID")
    first_name: str = Field(..., min_length=1, description="First name")
    last_name: str = Field(..., min_length=1, description="Last name")
    email: str = Field(..., description="Email address")
    department: str = Field(..., description="Department")
    position: str = Field(..., description="Job position")
    nationality: str = Field(..., description="Nationality")
    passport_number: str = Field(..., description="Passport number")
    passport_expiry: date = Field(..., description="Passport expiry date")
    date_of_birth: date = Field(..., description="Date of birth")
   
    @field_validator('passport_expiry')
    def validate_passport_expiry(cls, v):
        """Validate passport expiry date."""
        if v < date.today():
            raise ValueError("Passport has expired")
       
        # Check if passport expires within 6 months
        months_until_expiry = (v - date.today()).days / 30
        if months_until_expiry < 6:
            raise ValueError("Passport must be valid for at least 6 months from today")
       
        return v
   
    @field_validator('date_of_birth')
    def validate_date_of_birth(cls, v):
        """Validate date of birth."""
        if v >= date.today():
            raise ValueError("Date of birth must be in the past")
       
        age = (date.today() - v).days / 365.25
        if age < 18:
            raise ValueError("Applicant must be at least 18 years old")
       
        return v
   
    @field_validator('email')
    def validate_email(cls, v):
        """Validate email format."""

        if not v or '@' not in v:
            raise ValueError("Invalid email address")
        return v.lower()
 

class ApplicantPatch(BaseModel):
    """Applicant information model."""
    employee_id: Optional[str] = Field(None, description="Employee ID")
    first_name: Optional[str] = Field(None, min_length=1, description="First name")
    last_name: Optional[str] = Field(None, min_length=1, description="Last name")
    email: Optional[str] = Field(None, description="Email address")
    department: Optional[str] = Field(None, description="Department")
    position: Optional[str] = Field(None, description="Job position")
    nationality: Optional[str] = Field(None, description="Nationality")
    passport_number: Optional[str] = Field(None, description="Passport number")
    passport_expiry: Optional[date] = Field(None, description="Passport expiry date")
    date_of_birth: Optional[date] = Field(None, description="Date of birth")

    @field_validator('passport_expiry')
    def validate_passport_expiry(cls, v):
        """Validate passport expiry date."""
        if v is None:
            return v  # Skip validation if not provided

        if v < date.today():
            raise ValueError("Passport has expired")

        # Check if passport expires within 6 months
        months_until_expiry = (v - date.today()).days / 30
        if months_until_expiry < 6:
            raise ValueError("Passport must be valid for at least 6 months from today")

        return v

    @field_validator('date_of_birth')
    def validate_date_of_birth(cls, v):
        """Validate date of birth."""
        if v is None:
            return v

        if v >= date.today():
            raise ValueError("Date of birth must be in the past")

        age = (date.today() - v).days / 365.25
        if age < 18:
            raise ValueError("Applicant must be at least 18 years old")

        return v

    @field_validator('email')
    def validate_email(cls, v):
        """Validate email format."""
        if v is None:
            return v

        if '@' not in v:
            raise ValueError("Invalid email address")
        return v.lower()
class TravelDetails(BaseModel):
    """Travel details model."""
    destination_country: str = Field(..., description="Destination country")
    purpose_of_travel: str = Field(..., description="Purpose of travel")
    departure_date: date = Field(..., description="Departure date")
    return_date: date = Field(..., description="Return date")
    duration_days: int = Field(..., ge=1, description="Duration in days")
    cities_to_visit: List[str] = Field(default_factory=list, description="Cities to visit")
   
    @field_validator('departure_date')
    def validate_departure_date(cls, v):
        """Validate departure date."""
        if v < date.today():
            raise ValueError("Departure date cannot be in the past")
       
        # Check if departure is at least 7 days from now (relaxed from 30)
        days_until_departure = (v - date.today()).days
        if days_until_departure < 7:
            raise ValueError("Departure date should be at least 7 days from now to allow processing time")
       
        return v
   
    @field_validator('return_date')
    def validate_return_date(cls, v, values):
        """Validate return date."""
        value = values.data.get("departure_date")
        if  value and v < value :
            raise ValueError("Return date cannot be before departure date")
        return v
   
    @field_validator('duration_days')
    def validate_duration(cls, v, values):
        """Validate duration matches dates."""
        value = values.data.get("departure_date")
        rd    = values.data.get("return_date")
        if  value and rd :
            calculated_duration = (rd - value).days + 1
            if abs(v - calculated_duration) > 1:  # Allow 1 day tolerance
                raise ValueError(f"Duration ({v} days) doesn't match travel dates ({calculated_duration} days)")
        return v
 
class Document(BaseModel):
    """Document model."""
    type: DocumentType = Field(..., description="Document type")
    filename: str = Field(..., description="Document filename")
    file_path: Optional[str] = Field(None, description="File storage path")
    uploaded_at: datetime = Field(default_factory=datetime.now, description="Upload timestamp")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    verified: bool = Field(default=False, description="Verification status")
   
    @field_validator('filename')
    def validate_filename(cls, v):
        """Validate filename."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Filename cannot be empty")
       
        # Check file extension
        allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx']
        if not any(v.lower().endswith(ext) for ext in allowed_extensions):
            raise ValueError(f"Invalid file type. Allowed: {', '.join(allowed_extensions)}")
       
        return v
 
class ApprovalHistory(BaseModel):
    """Approval history entry."""
    approver: str = Field(..., description="Approver name/ID")
    role: str = Field(..., description="Approver role (HR/Legal/Management)")
    action: str = Field(..., description="Action taken (approved/rejected)")
    timestamp: datetime = Field(default_factory=datetime.now, description="Action timestamp")
    comments: Optional[str] = Field(None, description="Approver comments")
 
class VisaApplication(BaseModel):
    """Main visa application model."""
    id: Optional[str] = Field(None, description="Application ID (auto-generated)")
    applicant: Applicant = Field(..., description="Applicant information")
    visa_type: str = Field(..., description="Type of visa (business/work/tourist/student)")
    travel_details: TravelDetails = Field(..., description="Travel details")
    documents: List[Document] = Field(default_factory=list, description="Uploaded documents")
    status: ApplicationStatus = Field(default=ApplicationStatus.DRAFT, description="Application status")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    submitted_at: Optional[datetime] = Field(None, description="Submission timestamp")
    current_approver: Optional[str] = Field(None, description="Current approver")
    approval_history: List[ApprovalHistory] = Field(default_factory=list, description="Approval history")
    notes: Optional[str] = Field(None, description="Additional notes")
    session_id: Optional[str] = Field(None, description="Session ID for tracking")
   
    # Additional fields for internal tracking (auto-populated)
    employee_id: Optional[str] = Field(None, description="Employee ID (duplicate for queries)")
    employee_name: Optional[str] = Field(None, description="Employee name (duplicate for queries)")
    destination_country: Optional[str] = Field(None, description="Destination (duplicate for queries)")
    purpose_of_travel: Optional[str] = Field(None, description="Purpose (duplicate for queries)")
    travel_dates: Optional[Dict[str, Any]] = Field(None, description="Travel dates (duplicate for queries)")
   
    # Approval tracking
    approval_status: str = Field(default="pending", description="Overall approval status")
    current_stage: str = Field(default="draft", description="Current workflow stage")
    hr_approval: Optional[Dict[str, Any]] = Field(None, description="HR approval details")
    legal_approval: Optional[Dict[str, Any]] = Field(None, description="Legal approval details")
    management_approval: Optional[Dict[str, Any]] = Field(None, description="Management approval details")
   
    @field_validator('visa_type')
    def validate_visa_type(cls, v):
        """Validate visa type."""
        allowed_types = ['business', 'work', 'tourist', 'student']
        if v.lower() not in allowed_types:
            raise ValueError(f"Invalid visa type. Allowed: {', '.join(allowed_types)}")
        return v.lower()
   
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }
 
class VisaRequirement(BaseModel):
    """Visa requirements model."""
    country: str
    visa_type: str
    required_documents: List[str]
    processing_time_days: int
    validity_months: int
    fees: Dict[str, float]
    special_requirements: List[str] = Field(default_factory=list)
    embassy_contacts: Dict[str, str] = Field(default_factory=dict)
 
# ============================================================================
# REQUEST/RESPONSE MODELS FOR API
# ============================================================================
 
class CreateApplicationRequest(BaseModel):
    """Request model for creating visa application."""
    applicant: Applicant
    visa_type: str
    travel_details: TravelDetails
    notes: Optional[str] = None
 
class CreateApplicationResponse(BaseModel):
    """Response model for created application."""
    success: bool
    message: str
    application_id: str
    session_id: str
    application: Optional[VisaApplication] = None
 
class DocumentValidationResult(BaseModel):
    """Document validation result."""
    complete: bool
    missing_documents: List[str] = Field(default_factory=list)
    invalid_documents: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
 
# Alias for backward compatibility
DocumentValidationResponse = DocumentValidationResult
 
class ApplicationStatusResponse(BaseModel):
    """Application status tracking response."""
    application_id: str
    current_status: str
    approval_status: str
    current_stage: str
    progress_percentage: int
    next_step: str
    estimated_completion: datetime
    timeline: List[Dict[str, Any]]
    approval_workflow: Dict[str, Any]

# ============================================================================
# PATCH/UPDATE MODELS
class VisaApplicationPatch(BaseModel):
    """Partial update model for VisaApplication."""
    id: Optional[str] = None
    applicant: Optional[ApplicantPatch] = None
    visa_type: Optional[str] = None
    travel_details: Optional[TravelDetails] = None
    documents: Optional[List[Document]] = None
    status: Optional[ApplicationStatus] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    current_approver: Optional[str] = None
    approval_history: Optional[List[ApprovalHistory]] = None
    notes: Optional[str] = None
    session_id: Optional[str] = None

    # Additional fields
    employee_id: Optional[str] = None
    employee_name: Optional[str] = None
    destination_country: Optional[str] = None
    purpose_of_travel: Optional[str] = None
    travel_dates: Optional[Dict[str, Any]] = None

    # Approval tracking
    approval_status: Optional[str] = None
    current_stage: Optional[str] = None
    hr_approval: Optional[Dict[str, Any]] = None
    legal_approval: Optional[Dict[str, Any]] = None
    management_approval: Optional[Dict[str, Any]] = None

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }
 
# ============================================================================
# LEGACY COMPATIBILITY (if needed for existing code)
# ============================================================================
 
# Alias for backward compatibility if you had different names
PersonalInfo = Applicant
TravelInfo = TravelDetails
DocumentValidationResponse = DocumentValidationResult
StatusResponse = ApplicationStatusResponse