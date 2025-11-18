from langchain.tools import tool
from typing import Dict, List
import requests
from src.api.models.approval_models import ApprovalRequest 
from src.api.models.visa_models import VisaApplicationPatch , CreateApplicationRequest , ApplicantTool , TravelDetailsTool , CreateApplicationArgsTool
from langchain_core.tools import StructuredTool
from typing import Optional
import requests
import json
from typing import Optional, List
from pydantic import BaseModel, Field
import streamlit as st

# base_url = "http://127.0.0.1:8001/"

base_url = "http://localhost:8001/"
endpoint_url = "http://localhost:8001/api/visa/applications"


@tool
def Get_Visa_Details(appid: str) -> Dict[str, List[str]]:
    """

    Retrieve the current status of a visa application.

    Args:
        application_id (str): The unique identifier of the visa application 
                              provided when the application was submitted.

    Returns:
        dict: A JSON object containing the visa application status details, such as:
            - application_id (str): The ID of the application.
            - Approval status (str): Current status (e.g., "Pending", "Approved", "Rejected").
            - updated_at (str): Timestamp of the last status update.

    Raises:
        requests.exceptions.RequestException: If the API call fails due to network issues or server errors.
        ValueError: If the application_id is invalid or not found.

    
    """
    print("Get_Visa_Details tool")
    endpoint_url = f"http://localhost:8001/api/visa/applications/{appid}"
    try:
        response = requests.get(endpoint_url, timeout=60)
        response.raise_for_status()
        print(f"> API Response ({response.status_code}): {response.json()}")
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"> Network/API error occurred: {e}")
        if e.response:
            print(f"> Server Response Body: {e.response.text}")
        return e.response.text

@tool
def Approve_Visa_Workflow(request: ApprovalRequest):
    """
    Approve or reject a visa application in the approval workflow. 
    
    need_arguments_eg:  {
  "application_id": "VISA-7A015FE6",
  "approver_id": "1102781",
  "approver_role": "legal",
  "action": "approve",
  "comments": "checking"
}
    """
    print("Approve_Visa_Workflow tool")
    endpoint_url = "http://localhost:8001/api/approvals/process"
    try:
        response = requests.post(endpoint_url, json=request.model_dump() , timeout=60)
        response.raise_for_status()
        print(f"> API Response ({response.status_code}): {response.json()}")
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"> Network/API error occurred: {e}")
        if e.response:
            print(f"> Server Response Body: {e.response.text}")
        return e.response.text



# --- All your Pydantic Models (ApplicantTool, etc.) remain the same ---
# (Assuming they are defined above this function)

def func(applicant: ApplicantTool, visa_type: str, travel_details: TravelDetailsTool, notes: Optional[str] = None) -> dict:
    """
    Creates a visa application by constructing a NESTED JSON payload that mirrors
    the API's expected schema and submits it.
    """
    print("\n--- Tool Called: submit_visa_application ---")

    try:
        # --- START: CORRECT NESTED PAYLOAD CREATION ---

        # The API is confirmed to expect a nested structure.
        # We will build the payload to exactly match the working curl command.

        # Step 1: Convert the Pydantic model arguments into dictionaries.
        # This is the crucial step to ensure the data is JSON-serializable.
        applicant_dict = applicant.model_dump()
        travel_details_dict = travel_details.model_dump()

        # Step 2: Construct the final nested payload.
        payload = {
            "applicant": applicant_dict,
            "visa_type": visa_type,
            "travel_details": travel_details_dict,
            "notes": notes
        }

        print(f"--- CORRECTLY NESTED API Payload ---\n{json.dumps(payload, indent=2)}\n")

        # --- END: CORRECT NESTED PAYLOAD CREATION ---

        endpoint_url = "http://localhost:8001/api/visa/applications"
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        print(f"> Sending POST request to {endpoint_url}...")
        response = requests.post(endpoint_url, json=payload, headers=headers, timeout=60)
        
        # Raise an exception for 4xx/5xx server errors
        response.raise_for_status()
        
        response_data = response.json()
        print(f"✅ API Success ({response.status_code}): {response_data}")

        # Update Streamlit UI on success
        if "application_id" in response_data:
            st.session_state.application_id = response_data["application_id"]
            st.session_state.applicant_name = f"{applicant.first_name} {applicant.last_name}"

        return response_data

    except requests.exceptions.HTTPError as http_err:
        # This block will give us the real error from the API
        status_code = http_err.response.status_code
        error_message = f"API Error: The server rejected the request with status code {status_code}."
        
        try:
            server_error_details = http_err.response.json()
            error_message += f" Server Response: {json.dumps(server_error_details)}"
        except json.JSONDecodeError:
            server_error_details = http_err.response.text
            error_message += f" Server Response (Non-JSON): {server_error_details}"
            
        print(f"❌ {error_message}")
        
        return {"error": error_message, "details": server_error_details}
        
    except Exception as e:
        error_msg = f"An unexpected error occurred in the tool function: {type(e).__name__} - {e}"
        print(f"❌ {error_msg}")
        return {"error": error_msg}


# --- Your StructuredTool definition remains the same ---
Create_Visa_Application = StructuredTool.from_function(
    func=func,
    name="submit_visa_application",
    description="Submit a visa application with all required applicant and travel details.",
    args_schema=CreateApplicationArgsTool
)



@tool
def rag_visa_query(query: str) :
    """
    Query the RAG knowledge base for Document needed to create visa for a country and to get embassy details .

    Args:
        query (str): The user's question regarding visa document requirements or embassy information.

    Returns:
        dict: A JSON object containing the answer, sources, and number of retrieved chunks.
    """
    print("RAG Query:", query)
    endpoint_url = "http://localhost:8001/api/rag/search"
    payload = {"query": query}

    try:
        response = requests.post(endpoint_url, json=payload, timeout=100)
        response.raise_for_status()
        print(f"> API Response ({response.status_code}): {response.json()}")
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"> Network/API error occurred: {e}")
        if e.response:
            print(f"> Server Response Body: {e.response.text}")
        return e.response.text
    


def update_application_data(**kwargs):
    """
    Update visa application data using keyword arguments.
    **remember to send application id in kwargs

    """
    patch = VisaApplicationPatch(**kwargs)  # Rebuild schema from kwargs
    application_id = patch.id
    if not application_id:
        raise ValueError("Application ID is required for update")

    update_data = patch.model_dump(exclude_unset=True)

    endpoint_url = f"http://localhost:8001/api/visa/applications/{application_id}"
    try:
        response = requests.patch(endpoint_url, json=update_data, timeout=60)
        response.raise_for_status()
        print(f"> API Response ({response.status_code}): {response.json()}")
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"> Network/API error occurred: {e}")
        if e.response:
            print(f"> Server Response Body: {e.response.text}")
        return e.response.text
    

patch_application = StructuredTool.from_function(
    func=update_application_data,
    name="patch_application_data",
    description="Updates a visa application with data provided in format , remeber to ask for application id in arguments",
    args_schema=VisaApplicationPatch
    )
# if __name__ == "__main__":
#     dd = {
#         "notes": "updated via tool"
#     }
#     update_application_data("VISA-7A015FE6", dd)


@tool
def update_embassy_status(application_id: str, status: str, embassy_name: Optional[str] = None, tracking_number: Optional[str] = None, notes: Optional[str] = None) -> dict:

    """

    Update embassy tracking status for a visa application.

    Args:

        application_id: The visa application ID

        status: Embassy status - must be one of: 'not_submitted', 'submitted', 'under_review', 'approved', 'rejected', 'visa_issued'

        embassy_name: Name of the embassy

        tracking_number: Tracking number for embassy submission

        notes: Additional notes about embassy status

    Returns:

        dict: Response with success status and embassy tracking details

    """

    print("update_embassy_status tool")

    endpoint_url = f"http://localhost:8001/api/visa/applications/{application_id}/embassy"

    request_data = {

        "status": status

    }

    if embassy_name:

        request_data["embassy_name"] = embassy_name

    if tracking_number:

        request_data["tracking_number"] = tracking_number

    if notes:

        request_data["notes"] = notes

    try:

        response = requests.put(endpoint_url, json=request_data, timeout=60)

        response.raise_for_status()

        print(f"> API Response ({response.status_code}): {response.json()}")

        return response.json()
 
    except requests.exceptions.RequestException as e:

        print(f"> Network/API error occurred: {e}")

        if e.response:

            print(f"> Server Response Body: {e.response.text}")

        return e.response.text
 

@tool
def get_embassy_status(application_id: str) -> dict:

    """

    Retrieve embassy tracking status for a visa application.

    Args:

        application_id: The visa application ID to retrieve embassy status for"""
    
    print("get_embassy_status tool")

    endpoint_url = f"http://localhost:8001/api/visa/applications/{application_id}/embassy"
    
    try:

        response = requests.get(endpoint_url, timeout=60)

        response.raise_for_status()

        print(f"> API Response ({response.status_code}): {response.json()}")

        return response.json()
 
    except requests.exceptions.RequestException as e:

        print(f"> Network/API error occurred: {e}")

        if e.response:

            print(f"> Server Response Body: {e.response.text}")

        return e.response.text
    

@tool
def validate_document_content(application_id: str) -> dict:

    """

    Validate if documents have content and are properly filled for a visa application.

    Args:

        application_id: The visa application ID to validate documents for

    Returns:

        dict: Document validation results including completeness and issues found

    """

    print("validate_document_content tool")

    endpoint_url = f"http://localhost:8001/api/visa/applications/{application_id}/validate-documents-content"

    try:

        response = requests.post(endpoint_url, timeout=60)

        response.raise_for_status()

        print(f"> API Response ({response.status_code}): {response.json()}")

        return response.json()
 
    except requests.exceptions.RequestException as e:

        print(f"> Network/API error occurred: {e}")

        if e.response:

            print(f"> Server Response Body: {e.response.text}")

        return e.response.text
 
@tool
def get_pending_approvals(approver_role: str) -> dict:
    """
    Get all visa applications pending approval for a specific approver role.

    Args:
        approver_role (str): The role of the approver (e.g., 'hr_team', 'legal_team', 'management_team', 'ceo')."""
    print("get_pending_approvals tool")
    endpoint_url = f"http://localhost:8001/api/approvals/pending?approver_role={approver_role}"
    try:
        response = requests.get(endpoint_url, timeout=60)
        response.raise_for_status()
        print(f"> API Response ({response.status_code}): {response.json()}")
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"> Network/API error occurred: {e}")
        if e.response:
            print(f"> Server Response Body: {e.response.text}")
        return e.response.text