# """
# RAG Service for knowledge retrieval
# Uses Azure OpenAI via LiteLLM for embeddings and chat
# """
 
import os
from typing import List, Dict, Any, Optional
from langchain_community.vectorstores import Milvus
from langchain_core.embeddings import Embeddings
from pymilvus import connections, utility
from litellm import completion, embedding
import numpy as np
import tempfile
import json
from datetime import datetime
 
# Azure OpenAI Configuration
AZURE_ENDPOINT = ""
AZURE_API_KEY = ""
AZURE_DEPLOYMENT_NAME = "gpt-4o"
AZURE_EMBEDDING_DEPLOYMENT = "text-embedding-3-small"
AZURE_API_VERSION = "2024-08-01-preview"
 
# Set environment variables for Azure OpenAI
os.environ["AZURE_API_KEY"] = AZURE_API_KEY
os.environ["AZURE_API_BASE"] = AZURE_ENDPOINT
os.environ["AZURE_API_VERSION"] = AZURE_API_VERSION
 
# Milvus connection details
MILVUS_ENDPOINT = ""
MILVUS_API_KEY = ""
 
class AzureOpenAIEmbeddings(Embeddings):
    """Azure OpenAI embeddings using LiteLLM"""
   
    def __init__(self, deployment_name: str = AZURE_EMBEDDING_DEPLOYMENT):
        self.deployment_name = deployment_name
        self.model = f"azure/{deployment_name}"
        print(f"✅ Initialized Azure OpenAI Embeddings: {self.model}")
   
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed documents using Azure OpenAI text-embedding-3-small"""
        try:
            # LiteLLM embedding call for Azure OpenAI
            response = embedding(
                model=self.model,
                input=texts,
                api_key=AZURE_API_KEY,
                api_base=AZURE_ENDPOINT,
                api_version=AZURE_API_VERSION
            )
           
            # Extract embeddings from response
            embeddings = [item['embedding'] for item in response.data]
            print(f"✅ Generated embeddings for {len(texts)} documents")
            return embeddings
           
        except Exception as e:
            print(f"❌ Error generating embeddings: {e}")
            # Fallback to simple embeddings if Azure fails
            return self._fallback_embeddings(texts)
   
    def embed_query(self, text: str) -> List[float]:
        """Embed query using Azure OpenAI"""
        try:
            response = embedding(
                model=self.model,
                input=[text],
                api_key=AZURE_API_KEY,
                api_base=AZURE_ENDPOINT,
                api_version=AZURE_API_VERSION
            )
            return response.data[0]['embedding']
           
        except Exception as e:
            print(f"❌ Error embedding query: {e}")
            return self._fallback_embeddings([text])[0]
   
    def _fallback_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Fallback embeddings if Azure fails"""
        import hashlib
        embeddings = []
        for text in texts:
            hash_obj = hashlib.md5(text.encode())
            hash_hex = hash_obj.hexdigest()
            # text-embedding-3-small has 1536 dimensions
            embedding = [float(int(hash_hex[i:i+2], 16)) / 255.0 for i in range(0, min(1536*2, len(hash_hex)), 2)]
            while len(embedding) < 1536:
                embedding.append(0.0)
            embeddings.append(embedding[:1536])
        return embeddings
 
class RAGService:
    def __init__(self):
        """Initialize RAG service with Azure OpenAI and Milvus."""
        # Azure OpenAI model for chat
        self.llm_model = f"azure/{AZURE_DEPLOYMENT_NAME}"
       
        # Milvus configuration
        self.milvus_endpoint = MILVUS_ENDPOINT
        self.milvus_api_key = MILVUS_API_KEY
       
        self.vectorstore = None
        self.is_connected = False
       
        try:
            print("🚀 Initializing RAG Service with Azure OpenAI...")
           
            # Initialize Vector Database
            self.setup_vector_db()
           
            # Sample visa knowledge base
            self.visa_documents = [
                "USA visa requires passport valid for 6 months, DS-160 form, and interview appointment",
                "UK visa requires biometric enrollment, financial proof, and accommodation details",
                "Schengen visa needs travel insurance covering 30,000 EUR and flight itinerary",
                "Business visa requires invitation letter from host company and company NOC",
                "Student visa needs admission letter and financial capability proof",
                "Tourist visa processing time is typically 15-30 working days",
                "Visa fees vary by country: USA $185, UK £115, Schengen €80",
                "Document checklist: passport photos, bank statements, employment verification",
                "Emergency visa processing available with additional fees and valid reasons",
                "Visa extension possible for valid reasons with proper documentation",
                "USA embassy in New Delhi: Shantipath, Chanakyapuri, New Delhi 110021, contact: +91-11-2419-8000",
                "UK embassy in Delhi: Shantipath, Chanakyapuri, New Delhi 110021, contact: +91-11-2419-2100",
                "Schengen visa application center in Delhi: DLF Corporate Park, Gurugram",
                "Recent update: USA introduced new visa fees effective January 2024",
                "UK updated biometric requirements for all visa categories in December 2023",
                "Work visa for USA requires H1B approval, valid job offer, and specialized occupation",
                "Canada work permit needs LMIA approval and job offer from Canadian employer",
                "Australia work visa categories include TSS 482, ENS 186, and working holiday visas",
                "Germany Blue Card for highly skilled workers requires salary threshold of €56,800",
                "Singapore Employment Pass needs monthly salary of SGD 5,000 minimum"
            ]
           
            self.load_knowledge_base()
            self.is_connected = True
            print("✅ RAG Service initialized successfully with Azure OpenAI")
           
        except Exception as e:
            print(f"❌ RAG Service initialization failed: {e}")
            self.is_connected = False
 
    def setup_vector_db(self):
        """Initialize Milvus connection and vector store"""
        try:
            connections.connect(
                alias="default",
                uri=self.milvus_endpoint,
                token=self.milvus_api_key
            )
            print("✅ Connected to Milvus")
           
            # List all existing collections
            existing_collections = utility.list_collections()
            print(f"📚 Existing collections: {existing_collections}")
           
            # Clean up old collections if we're at the limit
            if len(existing_collections) >= 5:
                print(f"⚠️  Collection limit reached ({len(existing_collections)}/5). Cleaning up old collections...")
                # Drop all collections except the one we want to keep
                for collection_name in existing_collections:
                    try:
                        utility.drop_collection(collection_name)
                        print(f"🗑️  Dropped collection: {collection_name}")
                    except Exception as e:
                        print(f"⚠️  Could not drop {collection_name}: {e}")
           
            # Initialize Azure OpenAI embeddings
            self.embedding_function = AzureOpenAIEmbeddings()
            self.collection_name = "visa_kb"  # Shorter name
           
            # Clean existing collection if it exists
            if utility.has_collection(self.collection_name):
                utility.drop_collection(self.collection_name)
                print(f"✅ Cleaned existing collection: {self.collection_name}")
               
        except Exception as e:
            print(f"❌ Error setting up vector database: {e}")
            raise
 
    def load_knowledge_base(self):
        """Load visa documents into vector database with Azure embeddings"""
        try:
            print("📚 Loading knowledge base with Azure OpenAI embeddings...")
            metadata = [
                {
                    "doc_type": "visa_requirement",
                    "source": "immigration_db",
                    "doc_id": i
                }
                for i in range(len(self.visa_documents))
            ]
           
            self.vectorstore = Milvus.from_texts(
                texts=self.visa_documents,
                embedding=self.embedding_function,
                metadatas=metadata,
                collection_name=self.collection_name,
                connection_args={
                    "uri": self.milvus_endpoint,
                    "token": self.milvus_api_key
                }
            )
            print(f"✅ Loaded {len(self.visa_documents)} visa documents with Azure embeddings")
           
        except Exception as e:
            print(f"❌ Error loading knowledge base: {e}")
            raise
 
    def add_documents(self, documents: List[str], metadata: List[Dict] = None):
        """
        Add documents to the knowledge base.
       
        Args:
            documents: List of document texts
            metadata: List of metadata dicts for each document
        """
        try:
            if not self.is_connected:
                raise ValueError("RAG service is not connected")
           
            if metadata is None:
                metadata = [{"source": "uploaded", "doc_type": "general"} for _ in documents]
           
            if len(documents) != len(metadata):
                raise ValueError("Documents and metadata must have the same length")
           
            # Add documents to vector store
            self.vectorstore.add_texts(
                texts=documents,
                metadatas=metadata
            )
           
            # Update local documents list
            if not hasattr(self, 'visa_documents'):
                self.visa_documents = []
           
            self.visa_documents.extend(documents)
           
            print(f"✅ Added {len(documents)} documents to knowledge base")
            return True
           
        except Exception as e:
            print(f"❌ Error adding documents: {e}")
            return False
 
    def get_document_count(self) -> int:
        """Get total number of documents in knowledge base."""
        try:
            if hasattr(self, 'visa_documents'):
                return len(self.visa_documents)
            return 0
        except:
            return 0
 
    def process_uploaded_file(self, file_path: str, filename: str) -> List[str]:
        """
        Process uploaded file and extract text content.
       
        Args:
            file_path: Path to the uploaded file
            filename: Original filename
           
        Returns:
            List of text chunks
        """
        try:
            file_extension = os.path.splitext(filename)[1].lower()
           
            if file_extension == '.pdf':
                return self._process_pdf_file(file_path)
            elif file_extension == '.txt':
                return self._process_text_file(file_path)
            elif file_extension == '.json':
                return self._process_json_file(file_path)
            elif file_extension in ['.doc', '.docx']:
                return self._process_doc_file(file_path)
            else:
                return self._process_generic_file(file_path)
               
        except Exception as e:
            print(f"❌ Error processing file {filename}: {e}")
            raise
 
    def _process_pdf_file(self, file_path: str) -> List[str]:
        """Extract text from PDF file."""
        try:
            # Try to use PyPDF2 first
            try:
                import PyPDF2
                documents = []
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page_num in range(len(pdf_reader.pages)):
                        page = pdf_reader.pages[page_num]
                        text = page.extract_text()
                        if text.strip():
                            # Split text into smaller chunks if needed
                            chunks = self._split_text_into_chunks(text)
                            documents.extend(chunks)
                return documents
            except ImportError:
                print("⚠️  PyPDF2 not available, trying pdfplumber...")
           
            # Fallback to pdfplumber if available
            try:
                import pdfplumber
                documents = []
                with pdfplumber.open(file_path) as pdf:
                    for page_num, page in enumerate(pdf.pages):
                        text = page.extract_text()
                        if text and text.strip():
                            chunks = self._split_text_into_chunks(text)
                            documents.extend(chunks)
                return documents
            except ImportError:
                print("⚠️  pdfplumber not available, using basic text extraction...")
           
            # Final fallback
            with open(file_path, 'rb') as file:
                content = file.read()
                text_content = content.decode('utf-8', errors='ignore')
                return self._split_text_into_chunks(text_content) if text_content.strip() else []
               
        except Exception as e:
            print(f"❌ PDF processing error: {e}")
            raise
 
    def _process_text_file(self, file_path: str) -> List[str]:
        """Process text file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            return self._split_text_into_chunks(content)
        except Exception as e:
            print(f"❌ Text file processing error: {e}")
            raise
 
    def _process_json_file(self, file_path: str) -> List[str]:
        """Process JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                json_content = json.load(file)
           
            # Convert JSON to text chunks
            if isinstance(json_content, list):
                documents = [str(item) for item in json_content]
            elif isinstance(json_content, dict):
                documents = [json.dumps(json_content, indent=2)]
            else:
                documents = [str(json_content)]
           
            return documents
           
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON file: {str(e)}")
        except Exception as e:
            print(f"❌ JSON processing error: {e}")
            raise
 
    def _process_doc_file(self, file_path: str) -> List[str]:
        """Process DOC/DOCX file."""
        try:
            # Try to use python-docx for DOCX files
            if file_path.endswith('.docx'):
                try:
                    import docx
                    doc = docx.Document(file_path)
                    full_text = []
                    for paragraph in doc.paragraphs:
                        if paragraph.text.strip():
                            full_text.append(paragraph.text)
                    text = '\n'.join(full_text)
                    return self._split_text_into_chunks(text) if text.strip() else []
                except ImportError:
                    print("⚠️  python-docx not available for DOCX processing")
           
            # Fallback for all document types
            with open(file_path, 'rb') as file:
                content = file.read()
                text_content = content.decode('utf-8', errors='ignore')
                return self._split_text_into_chunks(text_content) if text_content.strip() else []
               
        except Exception as e:
            print(f"❌ DOC processing error: {e}")
            raise
 
    def _process_generic_file(self, file_path: str) -> List[str]:
        """Process generic file types."""
        try:
            with open(file_path, 'rb') as file:
                content = file.read()
                text_content = content.decode('utf-8', errors='ignore')
                return self._split_text_into_chunks(text_content) if text_content.strip() else []
        except Exception as e:
            print(f"❌ Generic file processing error: {e}")
            raise
 
    def _split_text_into_chunks(self, text: str, chunk_size: int = 1000) -> List[str]:
        """Split text into chunks of specified size."""
        chunks = []
        start = 0
        text_length = len(text)
       
        while start < text_length:
            end = start + chunk_size
            if end < text_length:
                # Try to break at sentence end
                sentence_end = max(text.rfind('.', start, end),
                                 text.rfind('?', start, end),
                                 text.rfind('!', start, end))
                if sentence_end > start and sentence_end - start > chunk_size // 2:
                    end = sentence_end + 1
           
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
           
            start = end
       
        return chunks
 
    def retrieve_relevant_info(self, query: str, k: int = 3):
        """Retrieve relevant visa information from vector database"""
        try:
            if not self.is_connected:
                print("❌ RAG service not connected")
                return []
               
            
            # Ensure query is a string
            if not isinstance(query, str):
                print(f"❌ Invalid query type: {type(query)}. Expected string.")
                return []

            retriever = self.vectorstore.as_retriever(search_kwargs={"k": k})
            docs = retriever.invoke(query.strip())
            print(f"✅ Retrieved {len(docs)} relevant documents")
            return docs
           
        except Exception as e:
            print(f"❌ Error retrieving information: {e}")
            return []
 
    def generate_response(self, query: str, context_docs: Optional[List] = None) -> Dict[str, Any]:
        """Generate response using Azure OpenAI GPT-4o"""
        try:
            if not self.is_connected:
                return {
                    "answer": "RAG service is currently unavailable. Please try again later.",
                    "sources": [],
                    "tokens_used": 0
                }
           
            # Retrieve relevant documents if not provided
            if context_docs is None:
                context_docs = self.retrieve_relevant_info(query)
           
            # Build context from documents
            context = "\n".join([f"- {doc.page_content}" for doc in context_docs])
           
            # Create enhanced prompt
            prompt = f"""You are a professional Visa Desk Assistant for corporate immigration.
Answer the question based ONLY on the context below. Be precise, clear, and helpful.
 
Context:
{context}
 
Question: {query}
 
Provide a clear, structured answer about visa requirements and processes.
If the information is not in the context, say "I don't have specific information about this in my knowledge base."
"""
           
            # Generate response using Azure OpenAI via LiteLLM
            print(f"🤖 Generating response with Azure OpenAI: {AZURE_DEPLOYMENT_NAME}")
           
            response = completion(
                model=self.llm_model,
                messages=[{"role": "user", "content": prompt}],
                api_key=AZURE_API_KEY,
                api_base=AZURE_ENDPOINT,
                api_version=AZURE_API_VERSION,
                temperature=0.7,
                max_tokens=500
            )
           
            answer = response.choices[0].message.content
            tokens = response.usage.total_tokens
           
            print(f"✅ Generated response ({tokens} tokens)")
           
            return {
                "answer": answer,
                "sources": context_docs,
                "tokens_used": tokens,
                "model": AZURE_DEPLOYMENT_NAME
            }
           
        except Exception as e:
            print(f"❌ Error generating response: {e}")
            return {
                "answer": f"Sorry, I encountered an error: {str(e)}",
                "sources": [],
                "tokens_used": 0,
                "model": "error"
            }
 
    def query_visa_requirements(
        self,
        country: str,
        visa_type: str,
        additional_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Query visa requirements using RAG with Azure OpenAI.
       
        Args:
            country: Destination country
            visa_type: Type of visa
            additional_context: Optional additional context
       
        Returns:
            Dict with requirements and sources
        """
        try:
            # Create search query
            query_text = f"Visa requirements for {visa_type} visa to {country}"
            if additional_context:
                query_text += f". {additional_context}"
           
            print(f"🔍 Querying: {query_text}")
           
            # Generate response using RAG
            result = self.generate_response(query_text)
           
            return {
                "answer": result["answer"],
                "sources": [
                    {
                        "content": doc.page_content,
                        "metadata": doc.metadata
                    }
                    for doc in result["sources"]
                ],
                "retrieved_chunks": len(result["sources"]),
                "tokens_used": result.get("tokens_used", 0),
                "model_used": result.get("model", "unknown")
            }
           
        except Exception as e:
            print(f"❌ Error querying visa requirements: {e}")
            return {
                "answer": f"Sorry, I encountered an error while processing your query: {str(e)}",
                "sources": [],
                "retrieved_chunks": 0,
                "tokens_used": 0,
                "model_used": "error"
            }
 
    def get_embassy_information(
        self,
        country: str,
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get embassy information for a country using Azure OpenAI."""
        try:
            query_text = f"Embassy information and contact details for {country}"
            if location:
                query_text += f" in {location}"
           
            print(f"🏛️ Getting embassy info: {query_text}")
           
            # Retrieve relevant documents
            relevant_docs = self.retrieve_relevant_info(query_text, k=5)
           
            if not relevant_docs:
                return {
                    "information": f"No embassy information found for {country}. Please check official embassy websites.",
                    "sources": []
                }
           
            # Generate response
            result = self.generate_response(query_text, relevant_docs)
           
            return {
                "information": result["answer"],
                "sources": [
                    {
                        "content": doc.page_content,
                        "metadata": doc.metadata
                    }
                    for doc in result["sources"]
                ],
                "tokens_used": result.get("tokens_used", 0)
            }
           
        except Exception as e:
            print(f"❌ Error getting embassy information: {e}")
            return {
                "information": f"Sorry, I encountered an error: {str(e)}",
                "sources": []
            }
 
    def health_check(self) -> Dict[str, Any]:
        """Check RAG service health."""
        return {
            "connected": self.is_connected,
            "vector_store_ready": self.vectorstore is not None,
            "documents_loaded": self.get_document_count(),
            "collection_name": self.collection_name,
            "llm_model": AZURE_DEPLOYMENT_NAME,
            "embedding_model": AZURE_EMBEDDING_DEPLOYMENT,
            "azure_endpoint": AZURE_ENDPOINT
        }
 
    def chat(self, message: str, conversation_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Interactive chat with RAG context.
       
        Args:
            message: User message
            conversation_history: Optional conversation history
           
        Returns:
            Response with answer and context
        """
        try:
            # Retrieve relevant context
            context_docs = self.retrieve_relevant_info(message, k=5)
            context = "\n".join([doc.page_content for doc in context_docs])
           
            # Build messages with history
            messages = []
           
            # System message with context
            system_msg = f"""You are a professional Visa Desk Assistant. Use this knowledge base:
 
{context}
 
Provide clear, accurate answers based on the context. If unsure, say so."""
           
            messages.append({"role": "system", "content": system_msg})
           
            # Add conversation history if provided
            if conversation_history:
                messages.extend(conversation_history)
           
            # Add current message
            messages.append({"role": "user", "content": message})
           
            # Generate response
            response = completion(
                model=self.llm_model,
                messages=messages,
                api_key=AZURE_API_KEY,
                api_base=AZURE_ENDPOINT,
                api_version=AZURE_API_VERSION,
                temperature=0.7
            )
           
            return {
                "answer": response.choices[0].message.content,
                "sources": [{"content": doc.page_content} for doc in context_docs],
                "tokens_used": response.usage.total_tokens
            }
           
        except Exception as e:
            print(f"❌ Chat error: {e}")
            return {
                "answer": f"Sorry, I encountered an error: {str(e)}",
                "sources": [],
                "tokens_used": 0
            }
 
    def __del__(self):
        """Cleanup: disconnect from vector store."""
        try:
            if hasattr(self, 'vectorstore'):
                pass  # Milvus cleanup if needed
        except:
            pass
 
def cleanup_milvus_collections():
    """Utility function to cleanup all Milvus collections"""
    print("🧹 Cleaning up Milvus collections...")
    try:
        connections.connect(
            alias="cleanup",
            uri=MILVUS_ENDPOINT,
            token=MILVUS_API_KEY
        )
       
        collections = utility.list_collections()
        print(f"📚 Found {len(collections)} collections: {collections}")
       
        if not collections:
            print("✅ No collections to clean")
            return
       
        for collection_name in collections:
            try:
                utility.drop_collection(collection_name)
                print(f"🗑️  Dropped: {collection_name}")
            except Exception as e:
                print(f"⚠️  Error dropping {collection_name}: {e}")
       
        print("✅ Cleanup complete!")
       
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
 
def test_azure_rag():
    """Test RAG Service with Azure OpenAI"""
    print("🚀 Testing RAG Service with Azure OpenAI...\n")
   
    try:
        # Initialize service
        rag_service = RAGService()
       
        if not rag_service.is_connected:
            print("❌ RAG service not connected")
            return False
       
        # Test 1: Health check
        print("\n📊 Health Check:")
        health = rag_service.health_check()
        for key, value in health.items():
            print(f"  {key}: {value}")
       
        # Test 2: Query visa requirements
        print("\n🔍 Test Query: USA Business Visa")
        result = rag_service.query_visa_requirements("USA", "business")
        print(f"  Answer: {result['answer'][:200]}...")
        print(f"  Sources: {result['retrieved_chunks']}")
        print(f"  Tokens: {result['tokens_used']}")
        print(f"  Model: {result['model_used']}")
       
        # Test 3: Embassy information
        print("\n🏛️ Test Query: USA Embassy Info")
        embassy_info = rag_service.get_embassy_information("USA", "Delhi")
        print(f"  Info: {embassy_info['information'][:200]}...")
       
        print("\n✅ All tests passed!")
        return True
       
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
 
if __name__ == "__main__":
    test_azure_rag()