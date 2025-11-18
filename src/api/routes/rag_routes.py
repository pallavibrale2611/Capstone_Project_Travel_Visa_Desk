from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form
from typing import List, Optional
import logging
import time
import json
import os
import tempfile
from datetime import datetime
from fastapi import Body
from src.services.rag_service import RAGService
 
router = APIRouter(prefix="/api/rag", tags=["RAG Knowledge Base"])
logger = logging.getLogger(__name__)
 
# Dependency to get RAG service
def get_rag_service() -> RAGService:
    return RAGService()
 

from pydantic import BaseModel

class SearchRequest(BaseModel):
    query: str
    max_results: int = 5

@router.post(
    "/search",
    summary="Search Visa Knowledge Base",
    description="Search the RAG system for visa information and requirements"
)
async def search_visa_knowledge(
    query: SearchRequest,
    max_results: int = 5,
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Search the visa knowledge base using RAG.
   
    Args:
        query: Search query about visa requirements
        max_results: Maximum number of results to return (1-10)
       
    Returns:
        Search results with answer and sources
    """
    start_time = time.time()
   
    try:
        logger.info(f"Search query: {query}")
       
        if not rag_service.is_connected:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="RAG service is currently unavailable"
            )
       
        # Validate max_results
        if max_results < 1 or max_results > 10:
            max_results = 5
       
        # Retrieve relevant documents
        relevant_docs = rag_service.retrieve_relevant_info(query.query, k=max_results)
       
        # Generate response using RAG
        result = rag_service.generate_response(query)
       
        processing_time = time.time() - start_time
       
        # Format sources
        sources = []
        for doc in relevant_docs:
            sources.append({
                "content": doc.page_content,
                "metadata": getattr(doc, 'metadata', {}),
                "score": getattr(doc, 'score', None)
            })
       
        response = {
            "success": True,
            "query": query,
            "answer": result["answer"],
            "sources": sources,
            "total_results": len(sources),
            "processing_time": round(processing_time, 2),
            "tokens_used": result.get("tokens_used", 0),
            "model_used": result.get("model", "azure/gpt-4o")
        }
       
        logger.info(f"Search completed in {processing_time:.2f}s, found {len(sources)} results")
        return response
       
    except Exception as e:
        logger.error(f"Search error: {e}")
        processing_time = time.time() - start_time
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.post(
    "/upload",
    summary="Upload Document to Knowledge Base",
    description="Upload text or JSON documents to add to the visa knowledge base"
)
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form("visa_requirement"),
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Upload a document to the knowledge base.
   
    Args:
        file: Document file to upload (txt, json supported)
        document_type: Type of document (visa_requirement, embassy_info, etc.)
       
    Returns:
        Upload status and document info
    """
    start_time = time.time()
   
    try:
        logger.info(f"Uploading document: {file.filename}, type: {document_type}")
       
        if not rag_service.is_connected:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="RAG service is currently unavailable"
            )
       
        # Validate file type
        allowed_extensions = ['.txt', '.json']
        file_extension = os.path.splitext(file.filename)[1].lower()
       
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type {file_extension} not supported. Allowed: {', '.join(allowed_extensions)}"
            )
       
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
       
        try:
            # Process the file based on type
            if file_extension == '.txt':
                documents = await process_text_file(temp_file_path)
            elif file_extension == '.json':
                documents = await process_json_file(temp_file_path)
            else:
                documents = []
           
            # Add documents to knowledge base
            added_count = await add_documents_to_knowledge_base(
                documents, document_type, file.filename, rag_service
            )
           
            processing_time = time.time() - start_time
           
            response = {
                "success": True,
                "message": f"Successfully uploaded and processed {added_count} document chunks",
                "filename": file.filename,
                "file_type": file_extension,
                "document_type": document_type,
                "chunks_added": added_count,
                "processing_time": round(processing_time, 2)
            }
           
            logger.info(f"Upload completed: {file.filename}, added {added_count} chunks")
            return response
           
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
       
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        processing_time = time.time() - start_time
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )
 
async def process_text_file(file_path: str) -> List[str]:
    """Process text file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
       
        # Split text into chunks
        chunks = split_text_into_chunks(content)
        return chunks
       
    except Exception as e:
        logger.error(f"Text file processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process text file: {str(e)}"
        )
 
async def process_json_file(file_path: str) -> List[str]:
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON file: {str(e)}"
        )
    except Exception as e:
        logger.error(f"JSON processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process JSON file: {str(e)}"
        )
 
def split_text_into_chunks(text: str, chunk_size: int = 1000) -> List[str]:
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
 
async def add_documents_to_knowledge_base(
    documents: List[str],
    document_type: str,
    filename: str,
    rag_service: RAGService
) -> int:
    """
    Add documents to the knowledge base.
   
    Args:
        documents: List of document texts
        document_type: Type of documents
        filename: Original filename
       
    Returns:
        Number of documents added
    """
    try:
        if not documents:
            return 0
       
        # Prepare metadata for each document
        metadata_list = []
        for i, doc in enumerate(documents):
            metadata_list.append({
                "doc_type": document_type,
                "source": "uploaded_file",
                "filename": filename,
                "upload_timestamp": datetime.now().isoformat(),
                "chunk_id": i,
                "total_chunks": len(documents)
            })
       
        # Add to vector store using the service method
        success = rag_service.add_documents(documents, metadata_list)
       
        if success:
            logger.info(f"Added {len(documents)} document chunks to knowledge base")
            return len(documents)
        else:
            raise Exception("Failed to add documents to vector store")
       
    except Exception as e:
        logger.error(f"Error adding documents to knowledge base: {e}")
        raise
 
@router.get("/health")
async def health_check(rag_service: RAGService = Depends(get_rag_service)):
    """
    Simple health check for RAG service.
    """
    try:
        health = rag_service.health_check()
       
        return {
            "status": "healthy" if health["connected"] else "unhealthy",
            "connected": health["connected"],
            "vector_store_ready": health["vector_store_ready"],
            "documents_loaded": health["documents_loaded"],
            "collection_name": health["collection_name"],
            "timestamp": datetime.now().isoformat()
        }
       
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }
 
@router.get("/stats")
async def get_knowledge_base_stats(rag_service: RAGService = Depends(get_rag_service)):
    """
    Get knowledge base statistics.
    """
    try:
        health = rag_service.health_check()
       
        return {
            "total_documents": health["documents_loaded"],
            "collection_name": health["collection_name"],
            "vector_store_ready": health["vector_store_ready"],
            "service_connected": health["connected"],
            "last_updated": datetime.now().isoformat()
        }
       
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return {
            "error": str(e)
        }