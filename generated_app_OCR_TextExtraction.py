from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Callable, List, Optional, Tuple

import streamlit as st


def sanitize_filename(name: str) -> str:
    """
    Sanitize a filename for safe download use.

    Args:
        name: Original filename.

    Returns:
        A sanitized filename string.
    """
    base = Path(name).stem or "document"
    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "_", base).strip("._-")
    return sanitized or "document"


def ensure_pdf(filename: Optional[str], file_bytes: bytes) -> bool:
    """
    Validate that the uploaded content appears to be a PDF.

    Args:
        filename: Uploaded filename.
        file_bytes: Uploaded file bytes.

    Returns:
        True if the file appears to be a PDF, otherwise False.
    """
    has_pdf_extension = bool(filename and filename.lower().endswith(".pdf"))
    has_pdf_signature = file_bytes.startswith(b"%PDF")
    return has_pdf_extension and has_pdf_signature


def resolve_tesseract_command(custom_path: Optional[str]) -> Optional[str]:
    """
    Resolve the Tesseract executable path from a custom path or system PATH.

    Args:
        custom_path: Optional custom executable path.

    Returns:
        Resolved Tesseract command/path, or None if not found.
    """
    cleaned = (custom_path or "").strip()
    if cleaned:
        candidate = Path(cleaned)
        if candidate.exists() and candidate.is_file():
            return str(candidate)
        return None
    return shutil.which("tesseract")


def configure_tesseract(custom_path: Optional[str]) -> str:
    """
    Configure pytesseract to use a custom Tesseract binary path if provided.

    Args:
        custom_path: Path to the Tesseract executable.

    Returns:
        The resolved Tesseract command/path.

    Raises:
        ValueError: If the custom path is invalid or Tesseract cannot be found.
    """
    try:
        import pytesseract
    except Exception as exc:
        raise ValueError("pytesseract is not installed.") from exc

    resolved = resolve_tesseract_command(custom_path)
    if not resolved:
        if (custom_path or "").strip():
            raise ValueError("The provided Tesseract path does not exist or is not a file.")
        raise ValueError("Tesseract OCR binary not found on system PATH.")

    pytesseract.pytesseract.tesseract_cmd = resolved
    return resolved


def validate_ocr_setup(
    custom_tesseract_path: Optional[str],
    language: str,
) -> Tuple[bool, List[str], Optional[str]]:
    """
    Validate Python dependencies, Tesseract configuration, and OCR language availability.

    Args:
        custom_tesseract_path: Optional custom Tesseract executable path.
        language: Tesseract OCR language code.

    Returns:
        Tuple of:
            - whether validation succeeded
            - list of issues
            - resolved Tesseract path if available
    """
    issues: List[str] = []
    resolved_tesseract_path: Optional[str] = None

    try:
        import pytesseract
    except Exception:
        issues.append("Missing Python package: pytesseract")
        pytesseract = None  # type: ignore[assignment]

    try:
        import pdf2image  # noqa: F401
    except Exception:
        issues.append("Missing Python package: pdf2image")

    poppler_path = shutil.which("pdftoppm")
    if not poppler_path:
        issues.append(
            "Poppler utility 'pdftoppm' not found on system PATH. Install Poppler so pdf2image can render PDF pages."
        )

    if pytesseract is not None:
        resolved_tesseract_path = resolve_tesseract_command(custom_tesseract_path)
        if not resolved_tesseract_path:
            if (custom_tesseract_path or "").strip():
                issues.append("The provided Tesseract path does not exist or is not a file.")
            else:
                issues.append(
                    "Tesseract OCR binary not found on system PATH. Provide a custom Tesseract path or install Tesseract."
                )
        else:
            try:
                pytesseract.pytesseract.tesseract_cmd = resolved_tesseract_path
                pytesseract.get_tesseract_version()
            except Exception as exc:
                issues.append(f"Tesseract is configured but could not be executed: {exc}")

            cleaned_language = (language or "eng").strip()
            if cleaned_language:
                try:
                    available_languages = pytesseract.get_languages(config="")
                    if cleaned_language not in available_languages:
                        issues.append(
                            f"OCR language '{cleaned_language}' is not installed in Tesseract. "
                            f"Available languages: {', '.join(sorted(available_languages)) or 'none detected'}"
                        )
                except Exception as exc:
                    issues.append(f"Could not validate Tesseract languages: {exc}")

    return len(issues) == 0, issues, resolved_tesseract_path


def extract_text_from_pdf(
    pdf_bytes: bytes,
    dpi: int = 300,
    language: str = "eng",
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> List[str]:
    """
    Extract OCR text from each page of a PDF by converting pages to images.

    Args:
        pdf_bytes: PDF content as bytes.
        dpi: Rendering DPI for OCR.
        language: Tesseract OCR language code.
        progress_callback: Optional callback receiving (current_page, total_pages).

    Returns:
        A list of extracted text strings, one per page.

    Raises:
        RuntimeError: If PDF conversion or OCR fails.
    """
    try:
        from pdf2image import convert_from_bytes
    except Exception as exc:
        raise RuntimeError("Failed to import pdf2image. Please install the dependency.") from exc

    try:
        import pytesseract
    except Exception as exc:
        raise RuntimeError("Failed to import pytesseract. Please install the dependency.") from exc

    try:
        images = convert_from_bytes(pdf_bytes, dpi=dpi)
    except Exception as exc:
        raise RuntimeError(
            "Failed to read the PDF. Ensure the file is valid, readable, and that Poppler is installed."
        ) from exc

    if not images:
        raise RuntimeError("No pages were found in the uploaded PDF.")

    page_texts: List[str] = []
    total_pages = len(images)

    for idx, image in enumerate(images, start=1):
        if progress_callback:
            progress_callback(idx - 1, total_pages)
        try:
            text = pytesseract.image_to_string(image, lang=language)
            page_texts.append(text or "")
        except Exception as exc:
            raise RuntimeError(
                f"OCR failed on page {idx}. Check that Tesseract is installed and the language '{language}' is available. Details: {exc}"
            ) from exc
        if progress_callback:
            progress_callback(idx, total_pages)

    return page_texts


def normalize_text(text: str) -> str:
    """
    Normalize extracted OCR text for Markdown output.

    Args:
        text: Raw OCR text.

    Returns:
        Cleaned text.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def convert_pages_to_markdown(page_texts: List[str], source_name: str) -> str:
    """
    Convert extracted page text into a single Markdown document.

    Args:
        page_texts: OCR text for each page.
        source_name: Source PDF filename.

    Returns:
        Markdown document content.
    """
    title = sanitize_filename(source_name).replace("_", " ").strip() or "Extracted Document"
    sections: List[str] = [f"# {title}", ""]
    for idx, page_text in enumerate(page_texts, start=1):
        cleaned = normalize_text(page_text)
        sections.append(f"## Page {idx}")
        sections.append("")
        sections.append(cleaned if cleaned else "_No text extracted from this page._")
        sections.append("")
    return "\n".join(sections).strip() + "\n"


def save_uploaded_to_bytes(uploaded_file) -> bytes:
    """
    Read uploaded Streamlit file into bytes.

    Args:
        uploaded_file: Streamlit uploaded file object.

    Returns:
        File bytes.

    Raises:
        ValueError: If file cannot be read.
    """
    try:
        data = uploaded_file.getvalue()
    except Exception as exc:
        raise ValueError("Unable to read uploaded file.") from exc

    if not data:
        raise ValueError("The uploaded file is empty.")
    return data


def render_app() -> None:
    """
    Render the Streamlit OCR-to-Markdown application.
    """
    st.set_page_config(page_title="PDF OCR to Markdown", page_icon="📄", layout="wide")
    st.title("PDF OCR to Markdown")
    st.write("Upload a PDF file to extract text with Tesseract OCR and download the result as Markdown.")

    with st.expander("OCR Configuration", expanded=False):
        st.write("Optional: provide a custom Tesseract executable path if it is not available on your system PATH.")
        tesseract_path = st.text_input(
            "Tesseract binary path",
            value="",
            placeholder="e.g. /usr/bin/tesseract or C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
        )
        ocr_language = st.text_input("Tesseract language", value="eng", help="Example: eng")
        dpi = st.number_input("PDF render DPI", min_value=150, max_value=600, value=300, step=50)

    deps_ok, issues, resolved_tesseract = validate_ocr_setup(tesseract_path, ocr_language)

    if issues:
        st.warning("Please address the following setup issues before processing:")
        for issue in issues:
            st.write(f"- {issue}")
    elif resolved_tesseract:
        st.caption(f"Using Tesseract: {resolved_tesseract}")

    uploaded_file = st.file_uploader("Drag and drop a PDF here", type=["pdf"])

    if not uploaded_file:
        st.stop()

    try:
        pdf_bytes = save_uploaded_to_bytes(uploaded_file)
    except ValueError as exc:
        st.error(str(exc))
        st.stop()

    if not ensure_pdf(uploaded_file.name, pdf_bytes):
        st.error("Invalid upload. Please upload a valid PDF file with valid PDF content.")
        st.stop()

    process_clicked = st.button("Process PDF", type="primary", disabled=not deps_ok)

    if not process_clicked:
        st.stop()

    try:
        configure_tesseract(tesseract_path)
    except ValueError as exc:
        st.error(str(exc))
        st.stop()
    except Exception as exc:
        st.error(f"Failed to configure Tesseract path: {exc}")
        st.stop()

    progress = st.progress(0, text="Starting OCR processing...")
    status = st.empty()

    def update_progress(current: int, total: int) -> None:
        if total <= 0:
            progress.progress(0, text="Starting OCR processing...")
            return
        ratio = min(max(current / total, 0.0), 1.0)
        if current < total:
            status.info(f"Processing page {current + 1} of {total}...")
        else:
            status.info(f"Processed {total} of {total} pages...")
        progress.progress(ratio, text=f"OCR progress: {current}/{total} pages")

    try:
        with st.spinner("Running OCR on the uploaded PDF..."):
            page_texts = extract_text_from_pdf(
                pdf_bytes=pdf_bytes,
                dpi=int(dpi),
                language=(ocr_language or "eng").strip(),
                progress_callback=update_progress,
            )
        markdown_content = convert_pages_to_markdown(page_texts, uploaded_file.name)
        progress.empty()
        status.empty()
    except RuntimeError as exc:
        progress.empty()
        status.empty()
        st.error(str(exc))
        st.stop()
    except Exception as exc:
        progress.empty()
        status.empty()
        st.error(f"An unexpected error occurred during processing: {exc}")
        st.stop()

    output_filename = f"{sanitize_filename(uploaded_file.name)}.md"

    st.success("Markdown document generated successfully.")
    st.subheader("Markdown Preview")
    st.text_area("Extracted Markdown", value=markdown_content, height=400)

    st.download_button(
        label="Download Markdown",
        data=markdown_content.encode("utf-8"),
        file_name=output_filename,
        mime="text/markdown",
    )


def main() -> None:
    """
    Application entry point.
    """
    try:
        render_app()
    except Exception as exc:
        st.error(f"Application error: {exc}")


if __name__ == "__main__":
    main()