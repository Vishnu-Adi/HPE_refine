import os
import logging
import tempfile
from typing import Dict, Any, Optional, List
import hashlib
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("PDFDocHandler")

# Try to import PDF libraries with fallbacks
PDF_SUPPORT = True
PDF_METHOD = None

try:
    import pypdf
    PDF_METHOD = "pypdf"
    logger.info("Using pypdf for PDF extraction")
except ImportError:
    try:
        from pdfminer.high_level import extract_text as pdfminer_extract_text
        PDF_METHOD = "pdfminer"
        logger.info("Using pdfminer for PDF extraction")
    except ImportError:
        try:
            import textract
            PDF_METHOD = "textract"
            logger.info("Using textract for PDF extraction")
        except ImportError:
            PDF_SUPPORT = False
            logger.warning("No PDF extraction libraries found. PDF support is disabled.")
            logger.warning("Install one of: pypdf, pdfminer.six, or textract")


def extract_text_from_pdf(pdf_path: str) -> Optional[str]:
    """
    Extract text from a PDF file using available libraries.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted text or None if extraction failed
    """
    if not PDF_SUPPORT:
        logger.error("PDF support is not available. Please install a PDF library.")
        return None
    
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        return None
    
    try:
        if PDF_METHOD == "pypdf":
            return _extract_with_pypdf(pdf_path)
        elif PDF_METHOD == "pdfminer":
            return _extract_with_pdfminer(pdf_path)
        elif PDF_METHOD == "textract":
            return _extract_with_textract(pdf_path)
        else:
            logger.error("No PDF extraction method available")
            return None
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        return None


def _extract_with_pypdf(pdf_path: str) -> str:
    """Extract text using pypdf."""
    text_parts = []
    
    try:
        with open(pdf_path, 'rb') as file:
            reader = pypdf.PdfReader(file)
            
            # Get metadata
            meta = reader.metadata
            if meta:
                text_parts.append(f"Document Information:")
                if meta.get('/Title'):
                    text_parts.append(f"Title: {meta.get('/Title')}")
                if meta.get('/Subject'):
                    text_parts.append(f"Subject: {meta.get('/Subject')}")
                if meta.get('/Author'):
                    text_parts.append(f"Author: {meta.get('/Author')}")
                if meta.get('/CreationDate'):
                    text_parts.append(f"Creation Date: {meta.get('/CreationDate')}")
                text_parts.append("\n")
            
            # Extract text from pages
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    text_parts.append(f"Page {i+1}:")
                    text_parts.append(text)
                    text_parts.append("\n")
        
        return "\n".join(text_parts)
    
    except Exception as e:
        logger.error(f"Error with pypdf extraction: {e}")
        raise


def _extract_with_pdfminer(pdf_path: str) -> str:
    """Extract text using pdfminer."""
    try:
        return pdfminer_extract_text(pdf_path)
    except Exception as e:
        logger.error(f"Error with pdfminer extraction: {e}")
        raise


def _extract_with_textract(pdf_path: str) -> str:
    """Extract text using textract."""
    try:
        text = textract.process(pdf_path, method='pdfminer').decode('utf-8')
        return text
    except Exception as e:
        logger.error(f"Error with textract extraction: {e}")
        raise


def extract_metadata_from_pdf(pdf_path: str) -> Dict[str, Any]:
    """
    Extract metadata from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Dictionary of metadata
    """
    metadata = {
        "source_file": os.path.basename(pdf_path),
        "file_size_bytes": os.path.getsize(pdf_path),
        "extraction_date": datetime.now().isoformat()
    }
    
    if not PDF_SUPPORT:
        return metadata
    
    try:
        if PDF_METHOD == "pypdf":
            with open(pdf_path, 'rb') as file:
                reader = pypdf.PdfReader(file)
                
                # Get document info
                info = reader.metadata
                if info:
                    if info.get('/Title'):
                        metadata["title"] = info.get('/Title')
                    if info.get('/Author'):
                        metadata["author"] = info.get('/Author')
                    if info.get('/Subject'):
                        metadata["subject"] = info.get('/Subject')
                    if info.get('/Keywords'):
                        metadata["keywords"] = info.get('/Keywords')
                    if info.get('/CreationDate'):
                        metadata["creation_date"] = info.get('/CreationDate')
                
                # Add page count
                metadata["page_count"] = len(reader.pages)
                
    except Exception as e:
        logger.error(f"Error extracting PDF metadata: {e}")
    
    return metadata


def infer_financial_metadata(text: str) -> Dict[str, Any]:
    """
    Infer financial document metadata from extracted text.
    
    Args:
        text: Extracted text from financial document
        
    Returns:
        Dictionary of inferred metadata
    """
    import re
    
    metadata = {}
    
    # Look for quarter/year information
    q_match = re.search(r'Q([1-4])\s*(?:FY)?[\s\']?(\d{2,4})', text, re.IGNORECASE)
    if q_match:
        quarter = q_match.group(1)
        year = q_match.group(2)
        
        # Handle two-digit years
        if len(year) == 2:
            year = f"20{year}"
            
        metadata["quarter"] = f"Q{quarter}"
        metadata["fiscal_year"] = year
    
    # Look for financial indicators
    if re.search(r'annual\s+recurring\s+revenue|arr', text, re.IGNORECASE):
        metadata["contains_arr"] = True
    
    if re.search(r'greenlake', text, re.IGNORECASE):
        metadata["contains_greenlake"] = True
    
    if re.search(r'intelligent\s+edge', text, re.IGNORECASE):
        metadata["contains_intelligent_edge"] = True
    
    if re.search(r'hpc|high\s+performance\s+computing', text, re.IGNORECASE):
        metadata["contains_hpc"] = True
    
    # Try to determine document type
    if re.search(r'earnings\s+call|earnings\s+release|financial\s+results', text, re.IGNORECASE):
        metadata["document_type"] = "earnings"
    elif re.search(r'annual\s+report', text, re.IGNORECASE):
        metadata["document_type"] = "annual_report"
    elif re.search(r'investor\s+presentation', text, re.IGNORECASE):
        metadata["document_type"] = "investor_presentation"
    
    return metadata


def process_pdf_document(pdf_path: str) -> Dict[str, Any]:
    """
    Process a PDF document - extract text and metadata.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Dictionary with extracted text and metadata
    """
    if not PDF_SUPPORT:
        logger.error("PDF support is not available. Please install a PDF library.")
        return {"error": "PDF support not available"}
    
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        return {"error": "File not found"}
    
    try:
        # Extract text
        extracted_text = extract_text_from_pdf(pdf_path)
        if not extracted_text:
            return {"error": "Text extraction failed"}
        
        # Extract metadata
        metadata = extract_metadata_from_pdf(pdf_path)
        
        # For financial documents, infer additional metadata
        if "financial" in pdf_path.lower():
            financial_metadata = infer_financial_metadata(extracted_text)
            metadata.update(financial_metadata)
        
        return {
            "text": extracted_text,
            "metadata": metadata,
            "source_path": pdf_path
        }
    
    except Exception as e:
        logger.error(f"Error processing PDF document: {e}")
        return {"error": str(e)}


# Example usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python pdf_document_handler.py <pdf_file_path>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)
    
    if not pdf_path.lower().endswith('.pdf'):
        print(f"Error: Not a PDF file: {pdf_path}")
        sys.exit(1)
    
    print(f"Processing PDF file: {pdf_path}")
    
    if not PDF_SUPPORT:
        print("Error: PDF support is not available. Please install one of these libraries:")
        print("  pip install pypdf")
        print("  pip install pdfminer.six")
        print("  pip install textract")
        sys.exit(1)
    
    result = process_pdf_document(pdf_path)
    
    if "error" in result:
        print(f"Error: {result['error']}")
        sys.exit(1)
    
    print(f"\nMetadata:")
    for key, value in result["metadata"].items():
        print(f"  {key}: {value}")
    
    print(f"\nExtracted Text Preview (first 500 chars):")
    print(result["text"][:500] + "...")
    
    print(f"\nTotal Characters: {len(result['text'])}")
