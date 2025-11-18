
# ============================================================================
# FILE: src/services/visa_service.py
# Updated service with new request parameter structure
# ============================================================================
 
from typing import List, Dict, Any, Optional
from src.api.models.visa_models import (
    VisaApplication, ApplicationStatus, VisaRequirement,
    Document, DocumentType, Applicant, TravelDetails,
    CreateApplicationRequest, CreateApplicationResponse,
    DocumentValidationResult, ApplicationStatusResponse
)
from src.services.rag_service import RAGService
from src.services.approval_service import ApprovalService
import yaml
from datetime import datetime, timedelta, date
import uuid
import sqlite3
import json
import logging
from pydantic import ValidationError
 
class VisaService:
    def __init__(self, db_path: str = "visa_applications.db"):
        """Initialize visa service with dependencies and database."""
        self.rag_service = RAGService()
        self.approval_service = ApprovalService()
        self.logger = logging.getLogger(__name__)
       
        # Load configuration
        try:
            with open("config/visa_requirements.yaml", 'r') as f:
                self.config = yaml.safe_load(f)
        except FileNotFoundError:
            self.logger.warning("Configuration file not found, using defaults")
            self.config = {}
       
        # Initialize database
        self.db_path = db_path
        self._init_database()
       
        self.logger.info("VisaService initialized with database connection")
   
    def _init_database(self):
        """Initialize SQLite database with required tables."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
           
            # Create visa applications table with new structure
            cursor.execute('''CREATE TABLE IF NOT EXISTS visa_applications (
            id VARCHAR(50) PRIMARY KEY,
            visa_type VARCHAR(50) NOT NULL,
            status VARCHAR(20) DEFAULT 'submitted',
            approval_status VARCHAR(20) DEFAULT 'pending',
            current_stage VARCHAR(50),
            current_approver VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            submitted_at TIMESTAMP,
            notes TEXT,
            session_id varchar(50)
            
                );
            ''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS applicants (
            id SERIAL PRIMARY KEY,
            application_id VARCHAR(50) REFERENCES visa_applications(id) ON DELETE CASCADE,
            employee_id VARCHAR(20),
            first_name VARCHAR(50),
            last_name VARCHAR(50),
            email VARCHAR(100),
            department VARCHAR(50),
            position VARCHAR(50),
            nationality VARCHAR(50),
            passport_number VARCHAR(50),
            passport_expiry DATE,
            date_of_birth DATE
        );''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS travel_details (
            id SERIAL PRIMARY KEY,
            application_id VARCHAR(50) REFERENCES visa_applications(id) ON DELETE CASCADE,
            destination_country VARCHAR(50),
            purpose_of_travel VARCHAR(50),
            departure_date DATE,
            return_date DATE,
            duration_days INT
        );
                    ''')
            
            cursor.execute('''CREATE TABLE IF NOT EXISTS approval_history (
            id SERIAL PRIMARY KEY,
            application_id VARCHAR(50) REFERENCES visa_applications(id) ON DELETE CASCADE,
            approver VARCHAR(50),
            role VARCHAR(50),        -- HR, Legal, Management
            action VARCHAR(20),      -- approve/reject
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            comments TEXT
        );''')
           
            cursor.execute('''CREATE TABLE IF NOT EXISTS documents (
                id SERIAL PRIMARY KEY,
                application_id VARCHAR(50) REFERENCES visa_applications(id) ON DELETE CASCADE,
                document_name VARCHAR(100),
                document_url TEXT
            );''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS  embassy_tracking (
            id SERIAL PRIMARY KEY,        
            application_id VARCHAR(50) REFERENCES visa_applications(id) ON DELETE CASCADE,
            status VARCHAR(50) NOT NULL,
            embassy_name VARCHAR(100) NOT NULL,
            tracking_number VARCHAR(100),
            submission_date DATE,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
            
        );''')

            # Create indexes for better performance
            # cursor.execute('CREATE INDEX IF NOT EXISTS idx_employee_id ON visa_applications(employee_id)')
            # cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON visa_applications(status)')
            # cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_id ON visa_applications(session_id)')
            # cursor.execute('CREATE INDEX IF NOT EXISTS idx_destination ON visa_applications(destination_country)')
           
            conn.commit()
            conn.close()
            self.logger.info("Database initialized successfully")
           
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")
            raise
   
    # def create_application(
    #     self,
    #     request: CreateApplicationRequest
    # ) -> CreateApplicationResponse:
    #     """
    #     Create new visa application with validation.
       
    #     Args:
    #         request: CreateApplicationRequest with applicant, visa_type, travel_details
       
    #     Returns:
    #         CreateApplicationResponse with created application
    #     """
    #     try:
    #         # Create VisaApplication from request
    #         application = VisaApplication(
    #             applicant=request.applicant,
    #             visa_type=request.visa_type,
    #             travel_details=request.travel_details,
    #             notes=request.notes,
    #             status=ApplicationStatus.DRAFT
    #         )
           
    #         # Generate application ID and session ID
    #         application.id = f"VISA-{uuid.uuid4().hex[:8].upper()}"
    #         application.session_id = f"SESSION-{uuid.uuid4().hex[:12].upper()}"
    #         application.created_at = datetime.now()
    #         application.updated_at = datetime.now()
           
    #         # Auto-populate duplicate fields for querying
    #         application.employee_id = request.applicant.employee_id
    #         application.employee_name = f"{request.applicant.first_name} {request.applicant.last_name}"
    #         application.destination_country = request.travel_details.destination_country
    #         application.purpose_of_travel = request.travel_details.purpose_of_travel
    #         application.travel_dates = {
    #             'start': request.travel_details.departure_date.isoformat(),
    #             'end': request.travel_details.return_date.isoformat(),
    #             'duration': request.travel_details.duration_days
    #         }
           
    #         # Validate application
    #         self._validate_application(application)
           
    #         # Store in database
    #         self._save_to_database(application)
           
    #         self.logger.info(f"Application {application.id} created for employee {application.employee_id}")
           
    #         return CreateApplicationResponse(
    #             success=True,
    #             message="Visa application created successfully",
    #             application_id=application.id,
    #             session_id=application.session_id,
    #             application=application
    #         )
           
    #     except ValidationError as e:
    #         self.logger.error(f"Validation error: {e}")
    #         raise ValueError(f"Invalid application data: {e}")
    #     except Exception as e:
    #         self.logger.error(f"Application creation failed: {e}")
    #         raise

    def create_application(self, request: CreateApplicationRequest) -> CreateApplicationResponse:
        """
        Create a new visa application with validation and normalized DB structure.

        Args:
            request: CreateApplicationRequest containing applicant, visa_type, travel_details.

        Returns:
            CreateApplicationResponse with created application details.
        """
        try:
            # Generate IDs
            application_id = f"VISA-{uuid.uuid4().hex[:8].upper()}"
            session_id = f"SESSION-{uuid.uuid4().hex[:12].upper()}"
            created_at = datetime.now()
            updated_at = datetime.now()

            # Validate request
            self._validate_application(request)

            # Connect to DB
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

#  status VARCHAR,                   -- submitted, in-progress, approved, rejected
#     approval_status VARCHAR,          -- pending, approved, rejected
#     current_stage VARCHAR,            -- HR Approval, Legal Approval, Management Approva

            # Insert into visa_applications
            cursor.execute('''
                INSERT INTO visa_applications (
                    id, visa_type, status, approval_status, current_stage,
                    current_approver, created_at, updated_at, submitted_at, notes, session_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?)
            ''', (
                application_id,
                request.visa_type,
                "submitted",          # Initial status
                "pending",            # Initial approval status
                "hr_team",          # Initial stage
                "hr_pool",                 # No approver yet
                created_at.isoformat(),
                updated_at.isoformat(),
                None,
                request.notes,
                session_id
            ))

            # Insert into applicants
            cursor.execute('''
                INSERT INTO applicants (
                    application_id, employee_id, first_name, last_name, email,
                    department, position, nationality, passport_number,
                    passport_expiry, date_of_birth
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                application_id,
                request.applicant.employee_id,
                request.applicant.first_name,
                request.applicant.last_name,
                request.applicant.email,
                request.applicant.department,
                request.applicant.position,
                request.applicant.nationality,
                request.applicant.passport_number,
                request.applicant.passport_expiry.isoformat(),
                request.applicant.date_of_birth.isoformat()
            ))

            # Insert into travel_details
            cursor.execute('''
                INSERT INTO travel_details (
                    application_id, destination_country, purpose_of_travel,
                    departure_date, return_date, duration_days
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                application_id,
                request.travel_details.destination_country,
                request.travel_details.purpose_of_travel,
                request.travel_details.departure_date.isoformat(),
                request.travel_details.return_date.isoformat(),
                request.travel_details.duration_days
            ))

            conn.commit()
            conn.close()

            self.logger.info(f"Application {application_id} created successfully.")

            return CreateApplicationResponse(
                success=True,
                message="Visa application created successfully",
                application_id=application_id,
                session_id=session_id
            )

        except ValidationError as e:
            self.logger.error(f"Validation error: {e}")
            raise ValueError(f"Invalid application data: {e}")
        except sqlite3.Error as e:
            self.logger.error(f"Database error: {e}")
            raise ValueError(f"Failed to save application: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            raise ValueError(f"Failed to save application: {e}")
    
    def _save_to_database(self, application: VisaApplication):
            """Save application to database."""
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
            
                # Convert application to JSON for storage
                app_data = application.dict()
            
                # Recursively convert all dates/datetimes to strings
                def convert_dates(obj):
                    if isinstance(obj, dict):
                        return {k: convert_dates(v) for k, v in obj.items()}
                    elif isinstance(obj, list):
                        return [convert_dates(item) for item in obj]
                    elif isinstance(obj, (datetime, date)):
                        return obj.isoformat()
                    else:
                        return obj
            
                app_data = convert_dates(app_data)
            
                cursor.execute('''
                    INSERT INTO visa_applications (
                        id, session_id, employee_id, employee_name, destination_country,
                        visa_type, purpose_of_travel, departure_date, return_date, duration_days,
                        documents, status, approval_status, current_stage, current_approver,
                        hr_approval, legal_approval, management_approval, approval_history,
                        notes, application_data, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    application.id,
                    application.session_id,
                    application.employee_id,
                    application.employee_name,
                    application.destination_country,
                    application.visa_type,
                    application.purpose_of_travel,
                    application.travel_details.departure_date.isoformat(),
                    application.travel_details.return_date.isoformat(),
                    application.travel_details.duration_days,
                    json.dumps([doc.dict() for doc in application.documents]),
                    application.status.value if hasattr(application.status, 'value') else application.status,
                    application.approval_status,
                    application.current_stage,
                    application.current_approver,
                    json.dumps(application.hr_approval) if application.hr_approval else None,
                    json.dumps(application.legal_approval) if application.legal_approval else None,
                    json.dumps(application.management_approval) if application.management_approval else None,
                    json.dumps([ah.dict() for ah in application.approval_history]),
                    application.notes,
                    json.dumps(app_data),
                    application.created_at.isoformat(),
                    application.updated_at.isoformat()
                ))
            
                conn.commit()
                conn.close()
                self.logger.info(f"Application {application.id} saved to database")
            
            except sqlite3.Error as e:
                self.logger.error(f"Database save failed: {e}")
                raise ValueError(f"Failed to save application: {e}")
   
    # def get_application(self, application_id: str) -> Optional[VisaApplication]:
    #     """
    #     Retrieve application by ID.
       
    #     Args:
    #         application_id: Application ID
       
    #     Returns:
    #         VisaApplication or None
    #     """
    #     try:
    #         conn = sqlite3.connect(self.db_path)
    #         cursor = conn.cursor()
           
    #         cursor.execute('SELECT application_data FROM visa_applications WHERE id = ?', (application_id,))
    #         result = cursor.fetchone()
    #         conn.close()
           
    #         if result:
    #             app_data = json.loads(result[0])
               
    #             # Convert date strings back to date objects
    #             if 'applicant' in app_data:
    #                 if 'passport_expiry' in app_data['applicant']:
    #                     app_data['applicant']['passport_expiry'] = date.fromisoformat(app_data['applicant']['passport_expiry'])
    #                 if 'date_of_birth' in app_data['applicant']:
    #                     app_data['applicant']['date_of_birth'] = date.fromisoformat(app_data['applicant']['date_of_birth'])
               
    #             if 'travel_details' in app_data:
    #                 if 'departure_date' in app_data['travel_details']:
    #                     app_data['travel_details']['departure_date'] = date.fromisoformat(app_data['travel_details']['departure_date'])
    #                 if 'return_date' in app_data['travel_details']:
    #                     app_data['travel_details']['return_date'] = date.fromisoformat(app_data['travel_details']['return_date'])
               
    #             # Convert datetime strings
    #             for field in ['created_at', 'updated_at', 'submitted_at']:
    #                 if app_data.get(field):
    #                     app_data[field] = datetime.fromisoformat(app_data[field])
               
    #             application = VisaApplication(**app_data)
    #             self.logger.info(f"Retrieved application {application_id}")
    #             return application
    #         else:
    #             self.logger.warning(f"Application {application_id} not found")
    #             return None
               
    #     except Exception as e:
    #         self.logger.error(f"Failed to retrieve application {application_id}: {e}")
    #         return None
    def get_application(self, application_id: str) -> Optional[VisaApplication]:
        """
        Retrieve a visa application by ID from normalized tables.

        Args:
            application_id: The unique application ID (e.g., VISA-XXXXXX).

        Returns:
            VisaApplication object or None if not found.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Fetch main application details
            cursor.execute('''
                SELECT id, visa_type, status, approval_status, current_stage,
                    current_approver, created_at, updated_at, submitted_at, notes
                FROM visa_applications WHERE id = ?
            ''', (application_id,))
            app_row = cursor.fetchone()
            print(app_row,"app_row")
            if not app_row:
                self.logger.warning(f"Application {application_id} not found")
                return None

            # Fetch applicant details
            cursor.execute('''
                SELECT employee_id, first_name, last_name, email, department,
                    position, nationality, passport_number, passport_expiry, date_of_birth
                FROM applicants WHERE application_id = ?
            ''', (application_id,))
            applicant_row = cursor.fetchone()

            # Fetch travel details
            cursor.execute('''
                SELECT destination_country, purpose_of_travel, departure_date,
                    return_date, duration_days
                FROM travel_details WHERE application_id = ?
            ''', (application_id,))
            travel_row = cursor.fetchone()

            # Fetch approval history
            cursor.execute('''
                SELECT approver, role, action, timestamp, comments
                FROM approval_history WHERE application_id = ?
                ORDER BY timestamp ASC
            ''', (application_id,))
            approval_rows = cursor.fetchall()

            conn.close()

            # Build VisaApplication object
            application = {
                "id": app_row[0],
                "visa_type": app_row[1],
                "status": app_row[2],
                "approval_status": app_row[3],
                "current_stage": app_row[4],
                "current_approver": app_row[5],
                "created_at": datetime.fromisoformat(app_row[6]) if app_row[6] else None,
                "updated_at": datetime.fromisoformat(app_row[7]) if app_row[7] else None,
                "submitted_at": datetime.fromisoformat(app_row[8]) if app_row[8] else None,
                "notes": app_row[9],
                "applicant": {
                    "employee_id": applicant_row[0],
                    "first_name": applicant_row[1],
                    "last_name": applicant_row[2],
                    "email": applicant_row[3],
                    "department": applicant_row[4],
                    "position": applicant_row[5],
                    "nationality": applicant_row[6],
                    "passport_number": applicant_row[7],
                    "passport_expiry": date.fromisoformat(applicant_row[8]),
                    "date_of_birth": date.fromisoformat(applicant_row[9])
                } if applicant_row else None,
                "travel_details": {
                    "destination_country": travel_row[0],
                    "purpose_of_travel": travel_row[1],
                    "departure_date": date.fromisoformat(travel_row[2]),
                    "return_date": date.fromisoformat(travel_row[3]),
                    "duration_days": travel_row[4]
                } if travel_row else None,
                "approval_history": [
                    {
                        "approver": row[0],
                        "role": row[1],
                        "action": row[2],
                        "timestamp": datetime.fromisoformat(row[3]),
                        "comments": row[4]
                    } for row in approval_rows
                ]
            }

            self.logger.info(f"Retrieved application {application_id}")
            return VisaApplication(**application)

        except Exception as e:
            self.logger.error(f"Failed to retrieve application {application_id}: {e}")
            return None

    # def update_application(self, application: VisaApplication) -> bool:
    #     """Update existing application."""
    #     try:
    #         application.updated_at = datetime.now()
           
    #         conn = sqlite3.connect(self.db_path)
    #         cursor = conn.cursor()
           
    #         app_data = application.dict()
           
    #         # Recursively convert all dates/datetimes to strings
    #         def convert_dates(obj):
    #             if isinstance(obj, dict):
    #                 return {k: convert_dates(v) for k, v in obj.items()}
    #             elif isinstance(obj, list):
    #                 return [convert_dates(item) for item in obj]
    #             elif isinstance(obj, (datetime, date)):
    #                 return obj.isoformat()
    #             else:
    #                 return obj
           
    #         app_data = convert_dates(app_data)
           
    #         cursor.execute('''
    #             UPDATE visa_applications
    #             SET employee_name = ?, destination_country = ?, visa_type = ?,
    #                 purpose_of_travel = ?, departure_date = ?, return_date = ?,
    #                 duration_days = ?, documents = ?, status = ?, approval_status = ?,
    #                 current_stage = ?, current_approver = ?, hr_approval = ?,
    #                 legal_approval = ?, management_approval = ?, approval_history = ?,
    #                 notes = ?, application_data = ?, updated_at = ?, submitted_at = ?
    #             WHERE id = ?
    #         ''', (
    #             application.employee_name,
    #             application.destination_country,
    #             application.visa_type,
    #             application.purpose_of_travel,
    #             application.travel_details.departure_date.isoformat(),
    #             application.travel_details.return_date.isoformat(),
    #             application.travel_details.duration_days,
    #             json.dumps([doc.dict() for doc in application.documents]),
    #             application.status.value if hasattr(application.status, 'value') else application.status,
    #             application.approval_status,
    #             application.current_stage,
    #             application.current_approver,
    #             json.dumps(application.hr_approval) if application.hr_approval else None,
    #             json.dumps(application.legal_approval) if application.legal_approval else None,
    #             json.dumps(application.management_approval) if application.management_approval else None,
    #             json.dumps([ah.dict() for ah in application.approval_history]),
    #             application.notes,
    #             json.dumps(app_data),
    #             application.updated_at.isoformat(),
    #             application.submitted_at.isoformat() if application.submitted_at else None,
    #             application.id
    #         ))
           
    #         if cursor.rowcount == 0:
    #             conn.close()
    #             return False
           
    #         conn.commit()
    #         conn.close()
    #         self.logger.info(f"Application {application.id} updated")
    #         return True
               
    #     except Exception as e:
    #         self.logger.error(f"Failed to update application: {e}")
    #         return False

    def update_application(self, application: VisaApplication) -> bool:
        """Update existing visa application and related tables."""
        try:
            timestamp = datetime.now()
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # --- Update visa_applications ---
            cursor.execute('''
                UPDATE visa_applications
                SET visa_type = ?, status = ?, approval_status = ?, current_stage = ?, 
                    current_approver = ?, notes = ?, updated_at = ?, submitted_at = ?
                WHERE id = ?
            ''', (
                application.visa_type,
                application.status,
                application.approval_status,
                application.current_stage,
                application.current_approver,
                application.notes,
                timestamp.isoformat(),
                application.submitted_at.isoformat() if application.submitted_at else None,
                application.id
            ))

            # --- Update applicant details ---
            cursor.execute('''
                UPDATE applicants
                SET employee_id = ?, first_name = ?, last_name = ?, email = ?, department = ?, 
                    position = ?, nationality = ?, passport_number = ?, passport_expiry = ?, date_of_birth = ?
                WHERE application_id = ?
            ''', (
                application.applicant.employee_id,
                application.applicant.first_name,
                application.applicant.last_name,
                application.applicant.email,
                application.applicant.department,
                application.applicant.position,
                application.applicant.nationality,
                application.applicant.passport_number,
                application.applicant.passport_expiry.isoformat(),
                application.applicant.date_of_birth.isoformat(),
                application.id
            ))

            # --- Update travel details ---
            cursor.execute('''
                UPDATE travel_details
                SET destination_country = ?, purpose_of_travel = ?, departure_date = ?, return_date = ?, duration_days = ?
                WHERE application_id = ?
            ''', (
                application.travel_details.destination_country,
                application.travel_details.purpose_of_travel,
                application.travel_details.departure_date.isoformat(),
                application.travel_details.return_date.isoformat(),
                application.travel_details.duration_days,
                application.id
            ))

            # --- Update documents ---
            cursor.execute('DELETE FROM documents WHERE application_id = ?', (application.id,))
            for doc in application.documents:
                cursor.execute('''
                    INSERT INTO documents (application_id, document_name, document_url)
                    VALUES (?, ?, ?)
                ''', (application.id, doc.document_name, doc.document_url))

            conn.commit()
            conn.close()
            self.logger.info(f"Application {application.id} updated successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to update application: {e}")
            return False
   
    def validate_documents(self, application: VisaApplication) -> DocumentValidationResult:
        """
        Validate all documents in application.
       
        Args:
            application: VisaApplication with documents
       
        Returns:
            DocumentValidationResult
        """
        result = DocumentValidationResult(complete=True)
       
        # Get required documents for visa type
        required_docs = self._get_required_documents(application.visa_type)
       
        # Check for missing documents
        provided_doc_types = [doc.type.value if hasattr(doc.type, 'value') else doc.type for doc in application.documents]
       
        for req_doc in required_docs:
            if req_doc not in provided_doc_types:
                result.missing_documents.append(req_doc)
                result.complete = False
       
        # Validate individual documents
        for document in application.documents:
            doc_validation = self._validate_single_document(document, application)
           
            if not doc_validation["valid"]:
                result.invalid_documents.append({
                    "document": document.type,
                    "issues": doc_validation["issues"]
                })
                result.complete = False
           
            if doc_validation.get("warnings"):
                result.warnings.extend(doc_validation["warnings"])
       
        return result
   
    def submit_application(self, application_id: str) -> VisaApplication:
        """Submit application for approval."""
        try:
            application = self.get_application(application_id)
            if not application:
                raise ValueError(f"Application {application_id} not found")
           
            # Validate documents
            validation = self.validate_documents(application)
            if not validation.complete:
                raise ValueError(f"Cannot submit incomplete application. Missing: {validation.missing_documents}")
           
            # Update status
            application.status = ApplicationStatus.SUBMITTED
            application.submitted_at = datetime.now()
            application.updated_at = datetime.now()
            application.current_stage = "submitted"
           
            # Save to database
            if not self.update_application(application):
                raise ValueError("Failed to update application")
           
            # Initialize approval workflow
            self.approval_service.start_workflow(application)
           
            self.logger.info(f"Application {application_id} submitted")
            return application
           
        except Exception as e:
            self.logger.error(f"Failed to submit application: {e}")
            raise
   
    def track_application_status(self, application_id: str) -> ApplicationStatusResponse:
        """Track application status."""
        application = self.get_application(application_id)
        if not application:
            raise ValueError(f"Application {application_id} not found")
       
        approval_status = self.approval_service.get_workflow_status(application_id)
       
        return ApplicationStatusResponse(
            application_id=application_id,
            current_status=application.status.value if hasattr(application.status, 'value') else application.status,
            approval_status=application.approval_status,
            current_stage=application.current_stage,
            progress_percentage=self._calculate_progress(application),
            next_step=self._get_next_step(application),
            estimated_completion=datetime.now() + timedelta(days=5),
            timeline=self._build_timeline(application),
            approval_workflow=approval_status
        )
   
    def _validate_application(self, application: VisaApplication):
        """Validate application (Pydantic handles most validation)."""
        # Additional business logic validation
        if not application.visa_type:
            raise ValueError("Visa type is required")
       
        # Check passport validity for travel dates
        months_until_travel = (application.travel_details.departure_date - date.today()).days / 30
        months_until_passport_expiry = (application.applicant.passport_expiry - date.today()).days / 30
       
        if months_until_passport_expiry < months_until_travel + 6:
            raise ValueError("Passport must be valid for 6 months beyond return date")
   
    def _get_required_documents(self, visa_type: str) -> List[str]:
        """Get required documents for visa type."""
        base_docs = ["passport", "passport_photos", "employment_letter"]
       
        if visa_type == "business":
            base_docs.extend(["invitation_letter", "bank_statement", "flight_itinerary"])
        elif visa_type == "work":
            base_docs.extend(["employment_contract", "bank_statement", "qualification_certificates"])
        elif visa_type == "tourist":
            base_docs.extend(["hotel_booking", "flight_itinerary", "bank_statement"])
       
        return base_docs
   
    def _validate_single_document(self, document: Document, application: VisaApplication) -> Dict[str, Any]:
        """Validate single document."""
        result = {"valid": True, "issues": [], "warnings": []}
       
        if document.type == DocumentType.PASSPORT:
            months_valid = (application.applicant.passport_expiry - date.today()).days / 30
            if months_valid < 6:
                result["valid"] = False
                result["issues"].append("Passport expires within 6 months")
       
        return result
   
    def _calculate_progress(self, application: VisaApplication) -> int:
        """Calculate progress percentage."""
        stages = {'draft': 0, 'submitted': 25, 'hr_review': 50, 'legal_review': 75, 'approved': 100}
        return stages.get(application.current_stage, 0)
   
    def _get_next_step(self, application: VisaApplication) -> str:
        """Get next step."""
        next_steps = {
            'draft': 'Submit application',
            'submitted': 'Awaiting HR review',
            'hr_review': 'Awaiting legal review',
            'approved': 'Ready for embassy submission'
        }
        return next_steps.get(application.current_stage, 'Processing')
   
    def _build_timeline(self, application: VisaApplication) -> List[Dict[str, Any]]:
        """Build timeline."""
        timeline = [
            {"stage": "created", "completed": True, "date": application.created_at, "description": "Application created"}
        ]
       
        if application.submitted_at:
            timeline.append({"stage": "submitted", "completed": True, "date": application.submitted_at, "description": "Submitted for approval"})
       
        timeline.append({"stage": application.current_stage, "current": True, "description": f"In {application.current_stage} stage"})
       
        return timeline
 
    def patch_application(self, application_id: str, updates: dict) -> bool:
        """Partially update visa application and related tables."""
        try:
            timestamp = datetime.now()
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build dynamic SQL for visa_applications
            fields = []
            values = []
            for key in ["visa_type", "status", "approval_status", "current_stage", "current_approver", "notes", "submitted_at"]:
                if key in updates:
                    fields.append(f"{key} = ?")
                    values.append(updates[key])

            if fields:
                fields.append("updated_at = ?")
                values.append(timestamp.isoformat())
                values.append(application_id)
                cursor.execute(f"UPDATE visa_applications SET {', '.join(fields)} WHERE id = ?", values)

            # Handle related tables if keys exist
            print(updates, "patch data")
            if "applicant" in updates:
                applicant = updates["applicant"]
                applicant_fields = []
                applicant_values = []
                for key in ["employee_id", "first_name", "last_name", "email", "department", "position", "nationality", "passport_number", "passport_expiry", "date_of_birth"]:
                    if key in applicant:
                        print(updates,"patch data")
                        applicant_fields.append(f"{key} = ?")
                        applicant_values.append(applicant[key])
                if applicant_fields:
                    applicant_values.append(application_id)
                    cursor.execute(f"UPDATE applicants SET {', '.join(applicant_fields)} WHERE application_id = ?", applicant_values)

            if "travel_details" in updates:
                travel = updates["travel_details"]
                travel_fields = []
                travel_values = []
                for key in ["destination_country", "purpose_of_travel", "departure_date", "return_date", "duration_days"]:
                    if key in travel:
                        travel_fields.append(f"{key} = ?")
                        travel_values.append(travel[key])
                if travel_fields:
                    travel_values.append(application_id)
                    cursor.execute(f"UPDATE travel_details SET {', '.join(travel_fields)} WHERE application_id = ?", travel_values)

            if "documents" in updates:
                cursor.execute("DELETE FROM documents WHERE application_id = ?", (application_id,))
                for doc in updates["documents"]:
                    cursor.execute("INSERT INTO documents (application_id, document_name, document_url) VALUES (?, ?, ?)", (application_id, doc["document_name"], doc["document_url"]))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            self.logger.error(f"Failed to patch application: {e}")
            return False

    def update_embassy_status(self, application_id: str, request_data: dict) -> bool:
        """Update embassy tracking status - simplified version."""
        try:
            # Check if application exists
            application = self.get_application(application_id)
            if not application:
                raise ValueError(f"Application {application_id} not found")
           
            # Validate status
            valid_statuses = ['not_submitted', 'submitted', 'under_review', 'approved', 'rejected', 'visa_issued']
            status = request_data.get('status')
            if status not in valid_statuses:
                raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")
           
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
           
            # Check if embassy record exists
            cursor.execute('SELECT application_id FROM embassy_tracking WHERE application_id = ?', (application_id,))
            existing = cursor.fetchone()
           
            if existing:
                # Update existing record
                cursor.execute('''
                    UPDATE embassy_tracking
                    SET status = ?, embassy_name = ?, tracking_number = ?,
                        submission_date = ?, last_updated = ?, notes = ?
                    WHERE application_id = ?
                ''', (
                    status,
                    request_data.get('embassy_name'),
                    request_data.get('tracking_number'),
                    request_data.get('submission_date'),
                    datetime.now().isoformat(),
                    request_data.get('notes'),
                    application_id
                ))
            else:
                # Create new record
                cursor.execute('''
                    INSERT INTO embassy_tracking (
                        application_id, status, embassy_name, tracking_number,
                        submission_date, last_updated, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    application_id,
                    status,
                    request_data.get('embassy_name'),
                    request_data.get('tracking_number'),
                    request_data.get('submission_date'),
                    datetime.now().isoformat(),
                    request_data.get('notes')
                ))
           
            conn.commit()
            conn.close()
            self.logger.info(f"Embassy status updated for {application_id}: {status}")
            return True
           
        except Exception as e:
            self.logger.error(f"Failed to update embassy status: {e}")
            return False
 
    def get_embassy_status(self, application_id: str) -> Optional[dict]:
        """Get embassy tracking status."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
           
            result = cursor.execute('''
                SELECT status, embassy_name, tracking_number, submission_date, last_updated, notes
                FROM embassy_tracking WHERE application_id = ?
            ''', (application_id,))
            print(result,"result embassy status")
            
            result = cursor.fetchone()
            conn.close()
           
            if not result:
                return "NO DATA FOUND"
           
            return {
                "application_id": application_id,
                "status": result[0],
                "embassy_name": result[1],
                "tracking_number": result[2],
                "submission_date": result[3],
                "last_updated": result[4],
                "notes": result[5]
            }
           
        except Exception as e:
            self.logger.error(f"Error getting embassy status: {e}")
            return None
 
    def validate_document_content_enhanced(self, application_id: str) -> DocumentValidationResult:
        """
        Validate documents by checking both application data and documents table.
       
        Args:
            application_id: Application ID
           
        Returns:
            DocumentValidationResult with validation details
        """
        try:
            # Get application to check if it has documents in the model
            application = self.get_application(application_id)
            if not application:
                return DocumentValidationResult(
                    complete=False,
                    missing_documents=["All documents"],
                    invalid_documents=[],
                    warnings=["Application not found"]
                )
           
            # Check documents table
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                'SELECT document_name, document_url FROM documents WHERE application_id = ?',
                (application_id,)
            )
            table_documents = cursor.fetchall()
            conn.close()
           
            missing_documents = []
            invalid_documents = []
            warnings = []
           
            # Check if we have documents in either location
            has_application_docs = hasattr(application, 'documents') and application.documents and len(application.documents) > 0
            has_table_docs = len(table_documents) > 0
           
            if not has_application_docs and not has_table_docs:
                # No documents found anywhere
                return DocumentValidationResult(
                    complete=False,
                    missing_documents=["passport", "employment_letter", "supporting_documents"],
                    invalid_documents=[],
                    warnings=["No documents found in application data or documents table"]
                )
           
            # Validate documents from the table (primary source)
            if has_table_docs:
                for doc_name, doc_url in table_documents:
                    issues = []
                   
                    if not doc_name or len(doc_name.strip()) == 0:
                        issues.append("Document name is empty")
                   
                    if not doc_url or len(doc_url.strip()) == 0:
                        issues.append("Document URL/path is empty")
                   
                    if issues:
                        invalid_documents.append({
                            "document": doc_name or "unknown_document",
                            "issues": issues
                        })
           
            # If we have application docs but no table docs, it might be inconsistent
            if has_application_docs and not has_table_docs:
                warnings.append("Documents exist in application data but not in documents table - data inconsistency detected")
           
            # Check for common required documents
            required_docs = ["passport", "employment_letter"]
            found_doc_types = []
           
            for doc_name, doc_url in table_documents:
                doc_name_lower = doc_name.lower() if doc_name else ""
                if "passport" in doc_name_lower:
                    found_doc_types.append("passport")
                elif "employment" in doc_name_lower or "offer" in doc_name_lower:
                    found_doc_types.append("employment_letter")
           
            # Check for missing required documents
            for req_doc in required_docs:
                if req_doc not in found_doc_types:
                    missing_documents.append(req_doc)
           
            complete = len(missing_documents) == 0 and len(invalid_documents) == 0
           
            return DocumentValidationResult(
                complete=complete,
                missing_documents=missing_documents,
                invalid_documents=invalid_documents,
                warnings=warnings
            )
           
        except Exception as e:
            self.logger.error(f"Error in enhanced document validation: {e}")
            return DocumentValidationResult(
                complete=False,
                missing_documents=["All documents"],
                invalid_documents=[],
                warnings=[f"Validation error: {str(e)}"]
            )

# upload documents in documents table
    def upload_document(self, application_id: str, documents: List[Document]) :
        """Update documents for an application."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
           
            # Delete existing documents
            cursor.execute('DELETE FROM documents WHERE application_id = ?', (application_id,))
           
            # Insert new documents
            for document in documents:
                cursor.execute('''
                    INSERT INTO documents (application_id, document_name, document_url)
                    VALUES (?, ?, ?)
                ''', (
                    application_id,
                    document.filename,
                    document.file_path
                ))
           
            conn.commit()
            conn.close()
            self.logger.info(f"Documents updated for application {application_id}")
            return documents
           
        except Exception as e:
            self.logger.error(f"Failed to update documents: {e}")
            return documents
        
         