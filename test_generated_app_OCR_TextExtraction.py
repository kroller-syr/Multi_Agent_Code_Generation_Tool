import importlib.util
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest


def _load_target_module():
    current = Path(__file__).resolve()
    for path in current.parent.glob("*.py"):
        if path.name.startswith("test_"):
            continue
        source = path.read_text(encoding="utf-8")
        if "def sanitize_filename" in source and "def render_app" in source:
            spec = importlib.util.spec_from_file_location("target_module", path)
            module = importlib.util.module_from_spec(spec)
            assert spec.loader is not None
            sys.modules["target_module"] = module
            spec.loader.exec_module(module)
            return module
    raise RuntimeError("Could not find target module containing application code.")


@pytest.fixture
def app_module():
    return _load_target_module()


def test_sanitize_filename_replaces_invalid_chars_and_strips_edges(app_module):
    assert app_module.sanitize_filename("  my report (final)!?.pdf  ") == "my_report_final"


def test_sanitize_filename_returns_document_when_stem_becomes_empty(app_module):
    assert app_module.sanitize_filename("!!!.pdf") == "document"


def test_sanitize_filename_uses_document_for_empty_name(app_module):
    assert app_module.sanitize_filename("") == "document"


def test_ensure_pdf_true_for_pdf_extension_and_signature(app_module):
    assert app_module.ensure_pdf("sample.PDF", b"%PDF-1.7 test content") is True


def test_ensure_pdf_false_when_extension_is_not_pdf(app_module):
    assert app_module.ensure_pdf("sample.txt", b"%PDF-1.7 test content") is False


def test_ensure_pdf_false_when_signature_missing(app_module):
    assert app_module.ensure_pdf("sample.pdf", b"not a pdf") is False


def test_resolve_tesseract_command_returns_custom_path_when_valid_file(app_module, tmp_path):
    exe = tmp_path / "tesseract"
    exe.write_text("binary", encoding="utf-8")
    assert app_module.resolve_tesseract_command(str(exe)) == str(exe)


def test_resolve_tesseract_command_returns_none_for_invalid_custom_path(app_module):
    assert app_module.resolve_tesseract_command("/does/not/exist/tesseract") is None


def test_resolve_tesseract_command_uses_system_path_when_no_custom_path(app_module, monkeypatch):
    monkeypatch.setattr(app_module.shutil, "which", lambda name: "/usr/bin/tesseract" if name == "tesseract" else None)
    assert app_module.resolve_tesseract_command(None) == "/usr/bin/tesseract"


def test_configure_tesseract_sets_pytesseract_command(app_module, monkeypatch):
    fake_inner = SimpleNamespace(tesseract_cmd=None)
    fake_pytesseract = SimpleNamespace(pytesseract=fake_inner)

    monkeypatch.setitem(sys.modules, "pytesseract", fake_pytesseract)
    monkeypatch.setattr(app_module, "resolve_tesseract_command", lambda custom: "/custom/tesseract")

    resolved = app_module.configure_tesseract("/custom/tesseract")

    assert resolved == "/custom/tesseract"
    assert fake_inner.tesseract_cmd == "/custom/tesseract"


def test_configure_tesseract_raises_when_pytesseract_missing(app_module, monkeypatch):
    original_import = __import__

    def fake_import(name, *args, **kwargs):
        if name == "pytesseract":
            raise ImportError("missing")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import)

    with pytest.raises(ValueError, match="pytesseract is not installed"):
        app_module.configure_tesseract(None)


def test_configure_tesseract_raises_for_invalid_custom_path(app_module, monkeypatch):
    fake_pytesseract = SimpleNamespace(pytesseract=SimpleNamespace(tesseract_cmd=None))
    monkeypatch.setitem(sys.modules, "pytesseract", fake_pytesseract)
    monkeypatch.setattr(app_module, "resolve_tesseract_command", lambda custom: None)

    with pytest.raises(ValueError, match="provided Tesseract path does not exist"):
        app_module.configure_tesseract("/bad/path")


def test_configure_tesseract_raises_when_binary_not_found_on_path(app_module, monkeypatch):
    fake_pytesseract = SimpleNamespace(pytesseract=SimpleNamespace(tesseract_cmd=None))
    monkeypatch.setitem(sys.modules, "pytesseract", fake_pytesseract)
    monkeypatch.setattr(app_module, "resolve_tesseract_command", lambda custom: None)

    with pytest.raises(ValueError, match="Tesseract OCR binary not found on system PATH"):
        app_module.configure_tesseract(None)


def test_validate_ocr_setup_success(app_module, monkeypatch):
    fake_pytesseract = SimpleNamespace(
        pytesseract=SimpleNamespace(tesseract_cmd=None),
        get_tesseract_version=lambda: "5.0.0",
        get_languages=lambda config="": ["eng", "spa"],
    )
    fake_pdf2image = ModuleType("pdf2image")

    monkeypatch.setitem(sys.modules, "pytesseract", fake_pytesseract)
    monkeypatch.setitem(sys.modules, "pdf2image", fake_pdf2image)
    monkeypatch.setattr(app_module.shutil, "which", lambda name: {"pdftoppm": "/usr/bin/pdftoppm"}.get(name))
    monkeypatch.setattr(app_module, "resolve_tesseract_command", lambda custom: "/usr/bin/tesseract")

    ok, issues, resolved = app_module.validate_ocr_setup(None, "eng")

    assert ok is True
    assert issues == []
    assert resolved == "/usr/bin/tesseract"
    assert fake_pytesseract.pytesseract.tesseract_cmd == "/usr/bin/tesseract"


def test_validate_ocr_setup_collects_missing_dependencies_and_poppler_issue(app_module, monkeypatch):
    original_import = __import__

    def fake_import(name, *args, **kwargs):
        if name in {"pytesseract", "pdf2image"}:
            raise ImportError(name)
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import)
    monkeypatch.setattr(app_module.shutil, "which", lambda name: None)

    ok, issues, resolved = app_module.validate_ocr_setup(None, "eng")

    assert ok is False
    assert resolved is None
    assert "Missing Python package: pytesseract" in issues
    assert "Missing Python package: pdf2image" in issues
    assert any("pdftoppm" in issue for issue in issues)


def test_validate_ocr_setup_reports_invalid_custom_tesseract_path(app_module, monkeypatch):
    fake_pytesseract = SimpleNamespace(
        pytesseract=SimpleNamespace(tesseract_cmd=None),
        get_tesseract_version=lambda: "5.0.0",
        get_languages=lambda config="": ["eng"],
    )
    fake_pdf2image = ModuleType("pdf2image")

    monkeypatch.setitem(sys.modules, "pytesseract", fake_pytesseract)
    monkeypatch.setitem(sys.modules, "pdf2image", fake_pdf2image)
    monkeypatch.setattr(app_module.shutil, "which", lambda name: "/usr/bin/pdftoppm" if name == "pdftoppm" else None)
    monkeypatch.setattr(app_module, "resolve_tesseract_command", lambda custom: None)

    ok, issues, resolved = app_module.validate_ocr_setup("/bad/path", "eng")

    assert ok is False
    assert resolved is None
    assert "The provided Tesseract path does not exist or is not a file." in issues


def test_validate_ocr_setup_reports_missing_language(app_module, monkeypatch):
    fake_pytesseract = SimpleNamespace(
        pytesseract=SimpleNamespace(tesseract_cmd=None),
        get_tesseract_version=lambda: "5.0.0",
        get_languages=lambda config="": ["eng", "fra"],
    )
    fake_pdf2image = ModuleType("pdf2image")

    monkeypatch.setitem(sys.modules, "pytesseract", fake_pytesseract)
    monkeypatch.setitem(sys.modules, "pdf2image", fake_pdf2image)
    monkeypatch.setattr(app_module.shutil, "which", lambda name: "/usr/bin/pdftoppm" if name == "pdftoppm" else None)
    monkeypatch.setattr(app_module, "resolve_tesseract_command", lambda custom: "/usr/bin/tesseract")

    ok, issues, resolved = app_module.validate_ocr_setup(None, "spa")

    assert ok is False
    assert resolved == "/usr/bin/tesseract"
    assert any("OCR language 'spa' is not installed" in issue for issue in issues)


def test_validate_ocr_setup_reports_tesseract_execution_error(app_module, monkeypatch):
    def fail_version():
        raise RuntimeError("boom")

    fake_pytesseract = SimpleNamespace(
        pytesseract=SimpleNamespace(tesseract_cmd=None),
        get_tesseract_version=fail_version,
        get_languages=lambda config="": ["eng"],
    )
    fake_pdf2image = ModuleType("pdf2image")

    monkeypatch.setitem(sys.modules, "pytesseract", fake_pytesseract)
    monkeypatch.setitem(sys.modules, "pdf2image", fake_pdf2image)
    monkeypatch.setattr(app_module.shutil, "which", lambda name: "/usr/bin/pdftoppm" if name == "pdftoppm" else None)
    monkeypatch.setattr(app_module, "resolve_tesseract_command", lambda custom: "/usr/bin/tesseract")

    ok, issues, resolved = app_module.validate_ocr_setup(None, "eng")

    assert ok is False
    assert resolved == "/usr/bin/tesseract"
    assert any("could not be executed" in issue for issue in issues)


def test_validate_ocr_setup_reports_language_validation_error(app_module, monkeypatch):
    def fail_languages(config=""):
        raise RuntimeError("language lookup failed")

    fake_pytesseract = SimpleNamespace(
        pytesseract=SimpleNamespace(tesseract_cmd=None),
        get_tesseract_version=lambda: "5.0.0",
        get_languages=fail_languages,
    )
    fake_pdf2image = ModuleType("pdf2image")

    monkeypatch.setitem(sys.modules, "pytesseract", fake_pytesseract)
    monkeypatch.setitem(sys.modules, "pdf2image", fake_pdf2image)
    monkeypatch.setattr(app_module.shutil, "which", lambda name: "/usr/bin/pdftoppm" if name == "pdftoppm" else None)
    monkeypatch.setattr(app_module, "resolve_tesseract_command", lambda custom: "/usr/bin/tesseract")

    ok, issues, resolved = app_module.validate_ocr_setup(None, "eng")

    assert ok is False
    assert resolved == "/usr/bin/tesseract"
    assert any("Could not validate Tesseract languages" in issue for issue in issues)


def test_extract_text_from_pdf_returns_texts_and_reports_progress(app_module, monkeypatch):
    progress_calls = []
    images = ["img1", "img2"]

    fake_pdf2image = ModuleType("pdf2image")
    fake_pdf2image.convert_from_bytes = lambda pdf_bytes, dpi: images

    class FakeTesseract:
        def image_to_string(self, image, lang):
            return f"text-for-{image}-{lang}"

    monkeypatch.setitem(sys.modules, "pdf2image", fake_pdf2image)
    monkeypatch.setitem(sys.modules, "pytesseract", FakeTesseract())

    result = app_module.extract_text_from_pdf(
        b"%PDF data",
        dpi=200,
        language="eng",
        progress_callback=lambda current, total: progress_calls.append((current, total)),
    )

    assert result == ["text-for-img1-eng", "text-for-img2-eng"]
    assert progress_calls == [(0, 2), (1, 2), (1, 2), (2, 2)]


def test_extract_text_from_pdf_raises_when_pdf2image_missing(app_module, monkeypatch):
    original_import = __import__

    def fake_import(name, *args, **kwargs):
        if name == "pdf2image":
            raise ImportError("missing")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import)

    with pytest.raises(RuntimeError, match="Failed to import pdf2image"):
        app_module.extract_text_from_pdf(b"%PDF")


def test_extract_text_from_pdf_raises_when_pytesseract_missing(app_module, monkeypatch):
    fake_pdf2image = ModuleType("pdf2image")
    fake_pdf2image.convert_from_bytes = lambda pdf_bytes, dpi: ["img1"]
    monkeypatch.setitem(sys.modules, "pdf2image", fake_pdf2image)

    original_import = __import__

    def fake_import(name, *args, **kwargs):
        if name == "pytesseract":
            raise ImportError("missing")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import)

    with pytest.raises(RuntimeError, match="Failed to import pytesseract"):
        app_module.extract_text_from_pdf(b"%PDF")


def test_extract_text_from_pdf_raises_when_pdf_conversion_fails(app_module, monkeypatch):
    fake_pdf2image = ModuleType("pdf2image")

    def fail_convert(pdf_bytes, dpi):
        raise RuntimeError("bad pdf")

    fake_pdf2image.convert_from_bytes = fail_convert
    monkeypatch.setitem(sys.modules, "pdf2image", fake_pdf2image)
    monkeypatch.setitem(sys.modules, "pytesseract", SimpleNamespace(image_to_string=lambda image, lang: "text"))

    with pytest.raises(RuntimeError, match="Failed to read the PDF"):
        app_module.extract_text_from_pdf(b"%PDF")


def test_extract_text_from_pdf_raises_when_no_pages_found(app_module, monkeypatch):
    fake_pdf2image = ModuleType("pdf2image")
    fake_pdf2image.convert_from_bytes = lambda pdf_bytes, dpi: []
    monkeypatch.setitem(sys.modules, "pdf2image", fake_pdf2image)
    monkeypatch.setitem(sys.modules, "pytesseract", SimpleNamespace(image_to_string=lambda image, lang: "text"))

    with pytest.raises(RuntimeError, match="No pages were found"):
        app_module.extract_text_from_pdf(b"%PDF")


def test_extract_text_from_pdf_raises_when_ocr_fails_on_page(app_module, monkeypatch):
    fake_pdf2image = ModuleType("pdf2image")
    fake_pdf2image.convert_from_bytes = lambda pdf_bytes, dpi: ["img1", "img2"]

    def fake_ocr(image, lang):
        if image == "img2":
            raise RuntimeError("ocr boom")
        return "ok"

    monkeypatch.setitem(sys.modules, "pdf2image", fake_pdf2image)
    monkeypatch.setitem(sys.modules, "pytesseract", SimpleNamespace(image_to_string=fake_ocr))

    with pytest.raises(RuntimeError, match=r"OCR failed on page 2"):
        app_module.extract_text_from_pdf(b"%PDF", language="eng")


def test_normalize_text_normalizes_line_endings_and_collapses_extra_blank_lines(app_module):
    raw = "line1\r\n\r\n\r\nline2\rline3\n\n\n\nline4"
    assert app_module.normalize_text(raw) == "line1\n\nline2\nline3\n\nline4"


def test_convert_pages_to_markdown_formats_title_pages_and_empty_text(app_module):
    markdown = app_module.convert_pages_to_markdown(
        ["First page text", "   ", "Third\r\n\r\npage"],
        "my_file-name.pdf",
    )

    expected = (
        "# my file-name\n\n"
        "## Page 1\n\n"
        "First page text\n\n"
        "## Page 2\n\n"
        "_No text extracted from this page._\n\n"
        "## Page 3\n\n"
        "Third\n\npage\n"
    )
    assert markdown == expected


def test_save_uploaded_to_bytes_returns_file_bytes(app_module):
    uploaded = SimpleNamespace(getvalue=lambda: b"data")
    assert app_module.save_uploaded_to_bytes(uploaded) == b"data"


def test_save_uploaded_to_bytes_raises_when_read_fails(app_module):
    class BadUpload:
        def getvalue(self):
            raise OSError("cannot read")

    with pytest.raises(ValueError, match="Unable to read uploaded file"):
        app_module.save_uploaded_to_bytes(BadUpload())


def test_save_uploaded_to_bytes_raises_for_empty_data(app_module):
    uploaded = SimpleNamespace(getvalue=lambda: b"")
    with pytest.raises(ValueError, match="uploaded file is empty"):
        app_module.save_uploaded_to_bytes(uploaded)


def test_main_reports_application_error_via_streamlit(app_module, monkeypatch):
    errors = []
    monkeypatch.setattr(app_module, "render_app", lambda: (_ for _ in ()).throw(RuntimeError("fatal")))
    monkeypatch.setattr(app_module.st, "error", lambda message: errors.append(message))

    app_module.main()

    assert errors == ["Application error: fatal"]