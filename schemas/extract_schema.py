from pydantic import BaseModel


class PDFExtractResponse(BaseModel):
    """Response after extracting text from a PDF file."""
    text: str               # full extracted text
    page_count: int         # number of pages in the PDF
    char_count: int         # total character count of extracted text


class DocxExtractResponse(BaseModel):
    """Response after extracting text from a .docx Word document."""
    text: str               # full extracted text
    paragraph_count: int    # number of paragraphs in the document
    char_count: int         # total character count
