"""
Document parsing and section-level chunking.
Ensures numbered sections (e.g. 1.1, 7.1, 11.1) are preserved cleanly with full spans.
"""
import re
from typing import List
from collections import Counter
from app.models.clause import Chunk

def strip_page_headers_and_footers(page_texts: List[str]) -> List[str]:
    """
    Identifies and removes lines that repeat across pages (common headers/footers)
    as well as pagination artifacts like 'Page X of Y', 'Page X', etc.
    """
    if len(page_texts) <= 1:
        cleaned_pages = []
        for text in page_texts:
            lines = text.split('\n')
            clean = []
            for line in lines:
                l_str = line.strip()
                if re.match(r'^(?:page\s+\d+(?:\s+of\s+\d+)?|\d+\s*/\s*\d+|\d+)$', l_str, re.IGNORECASE):
                    continue
                clean.append(line)
            cleaned_pages.append('\n'.join(clean))
        return cleaned_pages

    edge_lines = []
    for page in page_texts:
        lines = [l.strip() for l in page.split('\n') if l.strip()]
        if len(lines) >= 1:
            edge_lines.append(lines[0])
        if len(lines) >= 2:
            edge_lines.append(lines[-1])
        if len(lines) >= 3:
            edge_lines.append(lines[1])
            edge_lines.append(lines[-2])

    line_counts = Counter(edge_lines)
    threshold = max(2, len(page_texts) * 0.4)
    repeating_headers_footers = {line for line, count in line_counts.items() if count >= threshold}

    cleaned_pages = []
    for page in page_texts:
        lines = page.split('\n')
        kept_lines = []
        for line in lines:
            l_str = line.strip()
            if l_str in repeating_headers_footers:
                continue
            if re.match(r'^(?:page\s+\d+(?:\s+(?:of|/)\s+\d+)?|\d+\s*/\s*\d+|\d+)$', l_str, re.IGNORECASE):
                continue
            kept_lines.append(line)
        cleaned_pages.append('\n'.join(kept_lines))

    return cleaned_pages

def split_into_sections_or_windows(text: str) -> List[Chunk]:
    """
    Splits contract text into logical sections by matching numbered clause headers:
    e.g., '1.', '1.1', 'Section 1', 'Article I', '7.1 Non-Compete', '11.1 Assignment'.
    """
    # Regex matching:
    # 1. 'Section 1', 'SECTION 1.1', 'Article II'
    # 2. '11.1', '1.1', '1.' at start of line or after double newline
    pattern = r'(?m)(?=^(?:SECTION\s+\d+(?:\.\d+)?|ARTICLE\s+[IVXLCDM]+|\d+\.\d*(?:\s+[A-Z]|\.)))'
    section_splits = re.split(pattern, text)
    
    meaningful_sections = [s.strip() for s in section_splits if len(s.strip()) > 25]
    
    chunks = []
    char_offset = 0
    
    if len(meaningful_sections) >= 2:
        # Pack 2-3 sections together per chunk (~500-800 words) so full clauses are never cut
        current_chunk_text = []
        current_word_count = 0
        
        for sec in meaningful_sections:
            sec_words = len(sec.split())
            if current_word_count + sec_words > 800 and current_chunk_text:
                full_chunk_str = '\n\n'.join(current_chunk_text)
                chunks.append(Chunk(
                    text=full_chunk_str,
                    char_start=char_offset,
                    char_end=char_offset + len(full_chunk_str)
                ))
                char_offset += len(full_chunk_str)
                current_chunk_text = [sec]
                current_word_count = sec_words
            else:
                current_chunk_text.append(sec)
                current_word_count += sec_words
                
        if current_chunk_text:
            full_chunk_str = '\n\n'.join(current_chunk_text)
            chunks.append(Chunk(
                text=full_chunk_str,
                char_start=char_offset,
                char_end=char_offset + len(full_chunk_str)
            ))
        return chunks

    # Fallback to paragraph grouping if contract has non-standard numbering
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    current_chunk = []
    current_count = 0
    
    for p in paragraphs:
        w_count = len(p.split())
        if current_count + w_count > 600 and current_chunk:
            chunk_body = '\n\n'.join(current_chunk)
            chunks.append(Chunk(
                text=chunk_body,
                char_start=char_offset,
                char_end=char_offset + len(chunk_body)
            ))
            char_offset += len(chunk_body)
            current_chunk = [p]
            current_count = w_count
        else:
            current_chunk.append(p)
            current_count += w_count
            
    if current_chunk:
        chunk_body = '\n\n'.join(current_chunk)
        chunks.append(Chunk(
            text=chunk_body,
            char_start=char_offset,
            char_end=char_offset + len(chunk_body)
        ))
        
    return chunks

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF pages, scrubbing headers and footers."""
    import pdfplumber
    import io
    page_texts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                page_texts.append(t)
                
    cleaned_pages = strip_page_headers_and_footers(page_texts)
    return '\n\n'.join(cleaned_pages)

def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from a DOCX file."""
    from docx import Document
    import io
    doc = Document(io.BytesIO(file_bytes))
    paragraphs = [para.text.strip() for para in doc.paragraphs if para.text.strip()]
    return '\n\n'.join(paragraphs)

def parse_document(file_bytes: bytes, content_type: str) -> str:
    """Parse PDF or DOCX file to plain text."""
    if 'pdf' in content_type.lower():
        return extract_text_from_pdf(file_bytes)
    elif 'word' in content_type.lower() or 'docx' in content_type.lower():
        return extract_text_from_docx(file_bytes)
    else:
        raw_text = file_bytes.decode('utf-8', errors='replace')
        return '\n\n'.join(strip_page_headers_and_footers([raw_text]))

def chunk_document(text: str) -> List[Chunk]:
    return split_into_sections_or_windows(text)
