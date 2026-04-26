import fitz


class PDFExtractionError(Exception):
    pass


def extract_text(file_path):
    try:
        text_parts = []
        with fitz.open(file_path) as document:
            if document.page_count == 0:
                raise PDFExtractionError("PDF has no pages.")

            for page in document:
                text_parts.append(page.get_text("text"))
    except PDFExtractionError:
        raise
    except Exception as exc:
        raise PDFExtractionError("Could not extract text from PDF.") from exc

    text = "\n".join(text_parts).strip()
    if not text:
        raise PDFExtractionError("PDF contains no extractable text.")

    return text
