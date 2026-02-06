"""Data ingestion module for ProcessIQ.

Provides loaders for CSV, Excel, documents (PDF, DOCX, etc.), and LLM-based normalization.

Example usage:
    >>> from processiq.ingestion import load_csv, load_excel, normalize_with_llm
    >>>
    >>> # Load from clean CSV
    >>> data = load_csv("process.csv", process_name="Expense Approval")
    >>>
    >>> # Load from Excel
    >>> data = load_excel("process.xlsx", sheet_name="Steps")
    >>>
    >>> # Parse any document (PDF, DOCX, etc.)
    >>> from processiq.ingestion import parse_document, parse_file
    >>> doc = parse_file("process.pdf")
    >>> data, result = normalize_with_llm(doc.text)
    >>>
    >>> # Normalize messy text with LLM
    >>> data, result = normalize_with_llm('''
    ...     1. Submit request (30 min)
    ...     2. Manager reviews (1-2 hours)
    ...     3. Finance approves (45 min)
    ... ''')
"""

from processiq.ingestion.csv_loader import (
    load_csv,
    load_csv_from_bytes,
)
from processiq.ingestion.docling_parser import (
    SUPPORTED_EXTENSIONS,
    DocumentChunk,
    ParsedDocument,
    parse_document,
    parse_file,
    parse_from_stream,
)
from processiq.ingestion.excel_loader import (
    list_sheets,
    load_excel,
    load_excel_from_bytes,
)
from processiq.ingestion.normalizer import (
    ClarificationNeeded,
    ExtractedStep,
    ExtractionResponse,
    ExtractionResult,
    normalize_dataframe_with_llm,
    normalize_parsed_document,
    normalize_with_llm,
)

__all__ = [
    "SUPPORTED_EXTENSIONS",
    "ClarificationNeeded",
    "DocumentChunk",
    "ExtractedStep",
    "ExtractionResponse",
    "ExtractionResult",
    "ParsedDocument",
    "list_sheets",
    "load_csv",
    "load_csv_from_bytes",
    "load_excel",
    "load_excel_from_bytes",
    "normalize_dataframe_with_llm",
    "normalize_parsed_document",
    "normalize_with_llm",
    "parse_document",
    "parse_file",
    "parse_from_stream",
]
