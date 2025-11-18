import requests
from src.api.models.visa_models import Applicant , TravelDetails ,CreateApplicationRequest


# base_url = "http://localhost:8001/"
# endpoint_url = "http://localhost:8001/api/visa/applications"

# def func(data:CreateApplicationRequest):
#     print("tool-->data : ", data)
#     name_parts = ["nitesh", "soni"]
#     first_name = name_parts[0]
#     last_name = name_parts[1] if len(name_parts) > 1 else ""

#     payload = {
#         "applicant": {
#             "employee_id": "1102781",
#             "first_name": first_name,
#             "last_name": last_name,
#             "email": f"{first_name}.{last_name}@tcs.com".lower(),
#             "department": "string",
#             "position": "string",
#             "nationality": "string",
#             "passport_number": "string",
#             "passport_expiry": "2026-11-20",
#             "date_of_birth": "2000-11-22"
#         },
#         "visa_type": "work",
#         "travel_details": {
#             "destination_country": "USA",
#             "purpose_of_travel": "work",
#             "departure_date": "2025-11-25",
#             "return_date": "2025-11-29",
#             "duration_days": 5,
#             "cities_to_visit": ["string"]
#         },
#         "notes": "string"
#     }

#     try:
#         response = requests.post(endpoint_url, json=payload, timeout=10)
#         response.raise_for_status()
#         print(f"> API Response ({response.status_code}): {response.json()}")
#         return response.json()

#     except requests.exceptions.RequestException as e:
#         print(f"> Network/API error occurred: {e}")
#         if e.response:
#             print(f"> Server Response Body: {e.response.text}")
#         return e.response.text
    

# visa_tool = StructuredTool.from_function(
#     func=func,
#     name="submit_visa_application",
# #     description="Submit a visa application with all required details",
# #     args_schema=CreateApplicationRequest
# #     )


# def Get_Visa_Status(appid: str) :
#     """
    
#     """
#     endpoint_url = f"http://localhost:8001/api/visa/applications/{appid}"
#     try:
#         response = requests.get(endpoint_url, timeout=10)
#         response.raise_for_status()
#         print(f"> API Response ({response.status_code}): {response.json()}")
#         return response.json()

#     except requests.exceptions.RequestException as e:
#         print(f"> Network/API error occurred: {e}")
#         if e.response:
#             print(f"> Server Response Body: {e.response.text}")
#         return e.response.text
# Get_Visa_Status("VISA-7A015FE6")

# def generate(
#         prompt: str,
#         model_type: str = "primary",
#         **kwargs
#     ) -> str:
#         """
#         Generate text using LiteLLM.
        
#         Args:
#             prompt: Input prompt
#             model_type: Type of model to use (primary, precise, creative)
#             **kwargs: Additional parameters to override config
        
#         Returns:
#             Generated text
#         """
#         model_config = self.config['models'].get(model_type, self.config['models']['primary'])
        
#         # Merge config with kwargs
#         params = {
#             'model': model_config['model_name'],
#             'messages': [{"role": "user", "content": prompt}],
#             'temperature': model_config.get('temperature', 0.7),
#             'max_tokens': model_config.get('max_tokens', 2048),
#             'top_p': model_config.get('top_p', 0.95),
#             **kwargs
#         }
        
#         try:
#             response = completion(**params)
#             return response.choices[0].message.content
#         except Exception as e:
#             # Try fallback models
#             for fallback_model in self.config['api_settings'].get('fallback_models', []):
#                 try:
#                     params['model'] = fallback_model
#                     response = completion(**params)
#                     return response.choices[0].message.content
#                 except:
#                     continue
#             raise e


# from litellm import completion, embedding
# from src.llm import litellm_client 

# lc = litellm_client.LiteLLMClient()

# print(lc.generate("whats up ?"))
        

# def create_application(self, request: CreateApplicationRequest) -> CreateApplicationResponse:
#     """
#     Create a new visa application with validation and normalized DB structure.

#     Args:
#         request: CreateApplicationRequest containing applicant, visa_type, travel_details.

#     Returns:
#         CreateApplicationResponse with created application details.
#     """
#     try:
#         # Generate IDs
#         application_id = f"VISA-{uuid.uuid4().hex[:8].upper()}"
#         session_id = f"SESSION-{uuid.uuid4().hex[:12].upper()}"
#         created_at = datetime.now()
#         updated_at = datetime.now()

#         # Validate request
#         self._validate_application(request)

#         # Connect to DB
#         conn = sqlite3.connect(self.db_path)
#         cursor = conn.cursor()

#         # Insert into visa_applications
#         cursor.execute('''
#             INSERT INTO visa_applications (
#                 id, visa_type, status, approval_status, current_stage,
#                 current_approver, created_at, updated_at, submitted_at, notes
#             ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#         ''', (
#             application_id,
#             request.visa_type,
#             "submitted",          # Initial status
#             "pending",            # Initial approval status
#             "Submitted",          # Initial stage
#             None,                 # No approver yet
#             created_at.isoformat(),
#             updated_at.isoformat(),
#             None,
#             request.notes
#         ))

#         # Insert into applicants
#         cursor.execute('''
#             INSERT INTO applicants (
#                 application_id, employee_id, first_name, last_name, email,
#                 department, position, nationality, passport_number,
#                 passport_expiry, date_of_birth
#             ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#         ''', (
#             application_id,
#             request.applicant.employee_id,
#             request.applicant.first_name,
#             request.applicant.last_name,
#             request.applicant.email,
#             request.applicant.department,
#             request.applicant.position,
#             request.applicant.nationality,
#             request.applicant.passport_number,
#             request.applicant.passport_expiry.isoformat(),
#             request.applicant.date_of_birth.isoformat()
#         ))

#         # Insert into travel_details
#         cursor.execute('''
#             INSERT INTO travel_details (
#                 application_id, destination_country, purpose_of_travel,
#                 departure_date, return_date, duration_days
#             ) VALUES (?, ?, ?, ?, ?, ?)
#         ''', (
#             application_id,
#             request.travel_details.destination_country,
#             request.travel_details.purpose_of_travel,
#             request.travel_details.departure_date.isoformat(),
#             request.travel_details.return_date.isoformat(),
#             request.travel_details.duration_days
#         ))

#         conn.commit()
#         conn.close()

#         self.logger.info(f"Application {application_id} created successfully.")

#         return CreateApplicationResponse(
#             success=True,
#             message="Visa application created successfully",
#             application_id=application_id,
#             session_id=session_id
#         )

#     except ValidationError as e:
#         self.logger.error(f"Validation error: {e}")
#         raise ValueError(f"Invalid application data: {e}")
#     except sqlite3.Error as e:
#         self.logger.error(f"Database error: {e}")
#         raise ValueError(f"Failed to save application: {e}")
#     except Exception as e:
#         self.logger.error(f"Unexpected error: {e}")
#         raise
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a helpful assistant for visa applications. Your name is VisaBot. Use the tools provided to assist with visa application creation, status retrieval, approval workflow, querying visa requirements and updating application data. Be friendly and professional."),
            ("human", "{input}")
     
        ]
    )

print("prompt-->",prompt.messages)