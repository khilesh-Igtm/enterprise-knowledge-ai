import logging
import uuid
import zipfile
from pathlib import Path, PurePosixPath

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

logger = logging.getLogger(__name__)

CHUNK_SIZE = 64 * 1024

ALLOWED_MIME_TYPES = {
    ".pdf": "application/pdf",
    ".docx": (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ),
    ".txt": "text/plain",
}


def get_storage_root() -> Path:
    root = Path(settings.STORAGE_DIR).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def resolve_storage_path(storage_key: str) -> Path:
    key = PurePosixPath(storage_key)

    if key.is_absolute() or ".." in key.parts or "\\" in storage_key:
        raise ValueError("Invalid storage key")

    root = get_storage_root()
    target = (root / Path(*key.parts)).resolve()

    if not target.is_relative_to(root):
        raise ValueError("Invalid storage key")

    return target


def validate_document_content(
    file_path: Path,
    extension: str,
) -> None:
    with file_path.open("rb") as file:
        header = file.read(8)

    if extension == ".pdf":
        if not header.startswith(b"%PDF-"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid PDF file content",
            )

    elif extension == ".docx":
        try:
            with zipfile.ZipFile(file_path) as archive:
                if "word/document.xml" not in archive.namelist():
                    raise ValueError("Missing Word document content")
                if archive.testzip() is not None:
                    raise ValueError("Corrupt DOCX archive")
        except (zipfile.BadZipFile, ValueError) as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid DOCX file content",
            ) from e

    elif extension == ".txt":
        try:
            with file_path.open("r", encoding="utf-8-sig") as file:
                for _line in file:
                    pass
        except UnicodeDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="TXT file must contain valid UTF-8 text",
            ) from e


async def save_upload(
    upload: UploadFile,
    knowledge_base_id: uuid.UUID,
) -> tuple[str, int, str]:
    original_filename = Path(upload.filename or "").name

    if not original_filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required",
        )

    extension = Path(original_filename).suffix.lower()

    if extension not in settings.ALLOWED_DOCUMENT_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF, DOCX and TXT files are supported",
        )

    storage_key = f"knowledge-bases/{knowledge_base_id}/{uuid.uuid4().hex}{extension}"

    destination = resolve_storage_path(storage_key)
    destination.parent.mkdir(parents=True, exist_ok=True)

    temporary_path = destination.with_name(f".{destination.name}.uploading")

    total_size = 0

    try:
        with temporary_path.open("xb") as output:
            while chunk := await upload.read(CHUNK_SIZE):
                total_size += len(chunk)

                if total_size > settings.MAX_UPLOAD_SIZE:
                    raise HTTPException(
                        status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                        detail="Document exceeds the 20 MB upload limit",
                    )

                output.write(chunk)

        if total_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty files cannot be uploaded",
            )

        validate_document_content(temporary_path, extension)

        temporary_path.replace(destination)

        return (
            storage_key,
            total_size,
            ALLOWED_MIME_TYPES[extension],
        )

    except Exception:
        temporary_path.unlink(missing_ok=True)
        destination.unlink(missing_ok=True)
        raise

    finally:
        await upload.close()


def delete_file(storage_key: str) -> None:
    try:
        file_path = resolve_storage_path(storage_key)
        file_path.unlink(missing_ok=True)

        parent = file_path.parent

        while parent != get_storage_root() and parent.exists():
            try:
                parent.rmdir()
            except OSError:
                break
            parent = parent.parent

    except (ValueError, OSError):
        logger.exception(
            "Could not delete stored document: %s",
            storage_key,
        )
        raise
