# PDF to Markdown OCR App

## Overview

This Streamlit app lets a user upload a PDF, runs OCR with Tesseract across all pages, converts the extracted text into a single Markdown document, previews the result, and offers the `.md` file for download.

### Features
- Drag-and-drop PDF upload
- Multi-page PDF processing
- OCR using Tesseract
- PDF-to-image conversion for scanned documents
- Markdown output generation
- In-app progress/status updates
- Downloadable `.md` file
- Friendly error handling for invalid files or missing dependencies

## How to Run

### Prerequisites
- Python 3.9+
- Tesseract OCR installed and available on `PATH`
- Poppler installed for `pdf2image`

### Install dependencies
```bash
pip install streamlit pytesseract pdf2image pillow
```

Optional text extraction fallback/support:
```bash
pip install pymupdf pdfplumber
```

### System dependencies

#### macOS
```bash
brew install tesseract poppler
```

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr poppler-utils
```

#### Windows
- Install **Tesseract OCR**
- Install **Poppler for Windows**
- Add both binaries to your system `PATH`

If needed, configure Tesseract explicitly in Python:
```python
pytesseract.pytesseract.tesseract_cmd = r"C:\Path\To\tesseract.exe"
```

### Start the app
```bash
streamlit run app.py
```

## Example Usage

1. Launch the app in Streamlit.
2. Drag and drop a `.pdf` file into the uploader.
3. The app validates the file and begins processing pages.
4. Each page is converted to an image and passed through Tesseract OCR.
5. Extracted text is combined into Markdown.
6. Review the Markdown preview in the app.
7. Click the download button to save the generated `.md` file.

### Example output filename
If the uploaded file is:

```text
invoice_scan.pdf
```

the downloaded file should be:

```text
invoice_scan.md
```

## Design Notes

- **UI:** Built with Streamlit for a simple local web interface.
- **OCR Pipeline:** Uses `pdf2image` to render PDF pages as images, then `pytesseract` to extract text.
- **Consistency:** A single OCR-first pipeline can be used for all pages, including scanned and text-based PDFs, to keep behavior predictable.
- **Markdown Generation:** Page text is concatenated into one Markdown document, optionally separated by page headings such as:
  ```md
  ## Page 1
  ```
- **File Handling:** Prefer in-memory bytes or temporary files only; do not persist uploads permanently.
- **Validation:** Reject non-PDF uploads and surface readable error messages.
- **Status Updates:** Use Streamlit progress bars/spinners while processing multi-page PDFs.
- **Failure Handling:** Detect and report:
  - missing Tesseract
  - missing Poppler
  - unreadable/corrupt PDFs
  - OCR exceptions
- **Extensibility:** Optional direct text extraction with PyMuPDF or pdfplumber can be added later, but the app should follow one consistent extraction path.

## Testing

### Manual test cases
- Upload a valid single-page scanned PDF
- Upload a valid multi-page scanned PDF
- Upload a text-based PDF
- Upload a mixed-content PDF
- Upload a non-PDF file and confirm validation error
- Test with Tesseract unavailable and confirm clear dependency error
- Test with Poppler unavailable and confirm clear conversion error
- Test a corrupt/unreadable PDF and confirm graceful failure
- Verify downloaded filename ends with `.md`
- Verify Markdown preview matches downloaded content

### Expected behavior
- All PDF pages are processed
- OCR text is combined into one Markdown document
- Progress/status is shown during processing
- Errors are user-friendly and non-crashing
- No command-line interaction is required once the app is running