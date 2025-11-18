"""
Load visa requirements and knowledge base into Milvus
Populates collections with initial data
"""

from src.vector_store.milvus_client import MilvusClient
from src.llm.litellm_client import LiteLLMClient
from src.utils.logger import setup_logging, get_logger
import json
from pathlib import Path

setup_logging()
logger = get_logger(__name__)

def load_sample_data():
    """Load sample visa requirements and knowledge base."""
    
    # Sample visa requirements data
    visa_requirements = [
        {
            "text": "United States B1 Business Visa Requirements: Valid passport with 6 months validity, two passport-size photos, DS-160 form, invitation letter from US company, proof of financial means, travel itinerary. Processing time: 10-15 business days. Fee: $160.",
            "metadata": {
                "country": "United States",
                "visa_type": "business",
                "category": "requirements",
                "last_updated": "2025-01-01"
            }
        },
        {
            "text": "United Kingdom Business Visa Requirements: Valid passport, passport photos, completed application form, invitation letter, bank statements (last 6 months), travel insurance, accommodation proof. Processing: 15 days. Fee: £95.",
            "metadata": {
                "country": "United Kingdom",
                "visa_type": "business",
                "category": "requirements",
                "last_updated": "2025-01-01"
            }
        },
        {
            "text": "Canada Business Visa Requirements: Valid passport (6 months), photographs, completed application, letter of invitation, proof of funds, return ticket. Online application available. Processing: 2-4 weeks. Fee: CAD $100.",
            "metadata": {
                "country": "Canada",
                "visa_type": "business",
                "category": "requirements",
                "last_updated": "2025-01-01"
            }
        },
        {
            "text": "Germany Schengen Business Visa: Valid passport, photos, travel insurance (€30,000 coverage), hotel reservations, flight itinerary, invitation from German company, financial proof. Processing: 15 days. Fee: €80.",
            "metadata": {
                "country": "Germany",
                "visa_type": "business",
                "category": "requirements",
                "last_updated": "2025-01-01"
            }
        },
        {
            "text": "Australia Business Visa Requirements: ETA or subclass 600 visa, valid passport, business documentation, financial evidence, health insurance. Online application. Processing: 1-20 days. Fee: AUD $145.",
            "metadata": {
                "country": "Australia",
                "visa_type": "business",
                "category": "requirements",
                "last_updated": "2025-01-01"
            }
        }
    ]
    
    # Embassy information data
    embassy_info = [
        {
            "text": "US Embassy New Delhi: Address: Shantipath, Chanakyapuri, New Delhi 110021. Phone: +91-11-2419-8000. Email: support-india@ustraveldocs.com. Working Hours: Mon-Fri 8:30 AM - 5:30 PM. Appointment required for visa applications.",
            "metadata": {
                "country": "United States",
                "location": "New Delhi",
                "category": "embassy_contact"
            }
        },
        {
            "text": "UK Visa Application Centre Mumbai: Address: 7th Floor, Marathon Futurex, Lower Parel, Mumbai 400013. Phone: +91-22-6629-8401. Email: info.in@vfshelpline.com. Working Hours: Mon-Fri 8:00 AM - 3:00 PM. Biometric appointment required.",
            "metadata": {
                "country": "United Kingdom",
                "location": "Mumbai",
                "category": "embassy_contact"
            }
        },
        {
            "text": "Canadian Visa Application Centre Delhi: Address: Worldmark 1, 8th Floor, Asset Area 11, Aerocity, New Delhi 110037. Phone: +91-11-4084-4200. Working Hours: Mon-Fri 8:00 AM - 4:00 PM. Online application submission.",
            "metadata": {
                "country": "Canada",
                "location": "Delhi",
                "category": "embassy_contact"
            }
        }
    ]
    
    # Document templates
    templates = [
        {
            "text": """EMPLOYMENT VERIFICATION LETTER TEMPLATE

Date: [DATE]

To Whom It May Concern,

This letter is to confirm that [EMPLOYEE_NAME] has been employed with [COMPANY_NAME] since [START_DATE] in the position of [POSITION].

Current Employment Details:
- Employee ID: [EMPLOYEE_ID]
- Department: [DEPARTMENT]
- Monthly Salary: [SALARY]
- Employment Type: Full-time

The purpose of this letter is to support [EMPLOYEE_NAME]'s visa application for business travel to [DESTINATION_COUNTRY]. The travel dates are from [DEPARTURE_DATE] to [RETURN_DATE].

During this trip, [EMPLOYEE_NAME] will be attending [PURPOSE].

We confirm that all travel expenses will be borne by [COMPANY_NAME] and the employee will return to resume duties after the trip.

Should you require any further information, please contact us.

Sincerely,
[MANAGER_NAME]
[MANAGER_TITLE]
[COMPANY_NAME]
[CONTACT_INFO]""",
            "metadata": {
                "template_type": "employment_letter",
                "category": "template"
            }
        },
        {
            "text": """INVITATION LETTER TEMPLATE

Date: [DATE]

[APPLICANT_NAME]
[APPLICANT_ADDRESS]

Dear [APPLICANT_NAME],

We are pleased to invite you to visit [COMPANY_NAME] in [COUNTRY] for business purposes.

Visit Details:
- Purpose: [PURPOSE_OF_VISIT]
- Duration: [DURATION]
- Dates: [START_DATE] to [END_DATE]
- Location: [ADDRESS]

During your visit, you will be involved in [ACTIVITIES].

Accommodation and local transportation will be arranged by [COMPANY_NAME].

We look forward to your visit and the opportunity to work together.

Sincerely,
[HOST_NAME]
[HOST_TITLE]
[COMPANY_NAME]
[CONTACT_DETAILS]""",
            "metadata": {
                "template_type": "invitation_letter",
                "category": "template"
            }
        }
    ]
    
    try:
        logger.info("Initializing clients...")
        milvus_client = MilvusClient()
        milvus_client.connect()
        
        llm_client = LiteLLMClient()
        
        # Load visa requirements
        logger.info("Loading visa requirements...")
        texts = [item["text"] for item in visa_requirements]
        embeddings = llm_client.batch_embeddings(texts)
        metadata = [item["metadata"] for item in visa_requirements]
        
        milvus_client.insert(
            collection_key="visa_requirements",
            embeddings=embeddings,
            texts=texts,
            metadata=metadata
        )
        logger.info(f"✓ Loaded {len(visa_requirements)} visa requirements")
        
        # Load embassy information
        logger.info("Loading embassy information...")
        texts = [item["text"] for item in embassy_info]
        embeddings = llm_client.batch_embeddings(texts)
        metadata = [item["metadata"] for item in embassy_info]
        
        milvus_client.insert(
            collection_key="embassy_info",
            embeddings=embeddings,
            texts=texts,
            metadata=metadata
        )
        logger.info(f"✓ Loaded {len(embassy_info)} embassy records")
        
        # Load templates
        logger.info("Loading document templates...")
        texts = [item["text"] for item in templates]
        embeddings = llm_client.batch_embeddings(texts)
        metadata = [item["metadata"] for item in templates]
        
        milvus_client.insert(
            collection_key="templates",
            embeddings=embeddings,
            texts=texts,
            metadata=metadata
        )
        logger.info(f"✓ Loaded {len(templates)} templates")
        
        milvus_client.disconnect()
        logger.info("✓ Knowledge base loaded successfully")
        
    except Exception as e:
        logger.error(f"Failed to load knowledge base: {str(e)}")
        raise

if __name__ == "__main__":
    load_sample_data()