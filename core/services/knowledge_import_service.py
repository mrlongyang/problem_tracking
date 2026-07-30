import uuid
from pathlib import Path

from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone

from core.models import (
    KnowledgeArticle,
    KnowledgeArticleImage,
    KnowledgeGuideVersion,
    Module,
)

from .knowledge_docx_parser import parse_docx


ALLOWED_IMAGE_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".bmp",
    ".webp",
}


def resolve_module(
    guide_version: KnowledgeGuideVersion,
    parsed_module_name: str,
) -> Module | None:
    """
    Use the module selected during upload first.

    If no module was selected, try to match the module name
    extracted from the Word document.
    """

    if guide_version.guide.module:
        return guide_version.guide.module

    module_name = (parsed_module_name or "").strip()

    if not module_name:
        return None

    return (
        Module.objects
        .filter(module_name__iexact=module_name)
        .first()
    )


def save_article_images(
    article: KnowledgeArticle,
    parsed_images,
) -> int:
    """
    Replace existing extracted screenshots with the latest images
    from the uploaded Word document.

    Returns the number of images saved.
    """

    # Remove old database records and old physical image files.
    for existing_image in article.images.all():
        if existing_image.image:
            existing_image.image.delete(save=False)

        existing_image.delete()

    saved_count = 0

    for image_index, parsed_image in enumerate(parsed_images):
        original_file_name = (
            parsed_image.file_name
            or f"image_{image_index}.png"
        )

        suffix = Path(original_file_name).suffix.lower()

        if suffix not in ALLOWED_IMAGE_SUFFIXES:
            suffix = ".png"

        error_code = article.error_code or "article"

        safe_file_name = (
            f"{error_code}_"
            f"{uuid.uuid4().hex[:12]}"
            f"{suffix}"
        )

        image_record = KnowledgeArticleImage(
            article=article,
            caption=f"Screenshot for {error_code}",
            display_order=image_index,
        )

        image_record.image.save(
            safe_file_name,
            ContentFile(parsed_image.data),
            save=False,
        )

        image_record.save()
        saved_count += 1

    return saved_count


@transaction.atomic
def import_guide_version(
    guide_version: KnowledgeGuideVersion,
) -> dict:
    """
    Parse one uploaded Word guide and import each detected error
    as one KnowledgeArticle row.

    Screenshots are saved as KnowledgeArticleImage records.
    """

    if not guide_version.source_file:
        raise ValueError(
            "The guide version does not contain a source file."
        )

    file_path = Path(
        guide_version.source_file.path
    )

    if not file_path.exists():
        raise FileNotFoundError(
            f"Source file was not found: {file_path}"
        )

    parsed_articles = parse_docx(file_path)

    imported_count = 0
    updated_count = 0
    failed_count = 0
    image_count = 0
    logs: list[str] = []

    guide_version.status = "processing"
    guide_version.total_articles = len(parsed_articles)
    guide_version.imported_articles = 0
    guide_version.skipped_articles = 0
    guide_version.failed_articles = 0
    guide_version.import_log = ""
    guide_version.completed_at = None

    guide_version.save(
        update_fields=[
            "status",
            "total_articles",
            "imported_articles",
            "skipped_articles",
            "failed_articles",
            "import_log",
            "completed_at",
        ]
    )

    if not parsed_articles:
        guide_version.status = "failed"
        guide_version.import_log = (
            "No troubleshooting articles were detected "
            "in the Word document."
        )
        guide_version.completed_at = timezone.now()

        guide_version.save(
            update_fields=[
                "status",
                "import_log",
                "completed_at",
            ]
        )

        return {
            "total": 0,
            "imported": 0,
            "updated": 0,
            "skipped": 0,
            "failed": 0,
            "images": 0,
            "logs": [
                "No troubleshooting articles were detected."
            ],
        }

    for article_data in parsed_articles:
        error_code = (
            article_data.error_code
            or ""
        ).strip()

        title = (
            article_data.title
            or ""
        ).strip()

        if not error_code and not title:
            failed_count += 1
            logs.append(
                "Skipped one record because both error code "
                "and title were empty."
            )
            continue

        try:
            module = resolve_module(
                guide_version,
                article_data.module_name,
            )

            article, created = (
                KnowledgeArticle.objects.update_or_create(
                    guide_version=guide_version,
                    error_code=error_code,
                    title=title,
                    defaults={
                        "module": module,
                        "function_name": (
                            article_data.function_name or ""
                        ).strip(),
                        "transaction_code": (
                            article_data.transaction_code or ""
                        ).strip(),
                        "root_cause": (
                            article_data.root_cause or ""
                        ).strip(),
                        "resolution": (
                            article_data.resolution or ""
                        ).strip(),
                        "is_published": True,
                    },
                )
            )

            saved_images = save_article_images(
                article,
                article_data.images,
            )

            image_count += saved_images

            if created:
                imported_count += 1
                action_text = "Imported"
            else:
                updated_count += 1
                action_text = "Updated"

            log_parts = [
                f"{action_text} {error_code or title}"
            ]

            log_parts.append(
                f"{saved_images} image(s)"
            )

            if article_data.warnings:
                log_parts.append(
                    "; ".join(article_data.warnings)
                )

            logs.append(
                " — ".join(log_parts)
            )

        except Exception as exc:
            failed_count += 1

            logs.append(
                f"{error_code or title}: "
                f"{type(exc).__name__}: {exc}"
            )

    successful_count = (
        imported_count + updated_count
    )

    if failed_count == 0:
        status = "completed"
    elif successful_count > 0:
        status = "partial"
    else:
        status = "failed"

    guide_version.status = status
    guide_version.total_articles = len(parsed_articles)

    # Newly created articles
    guide_version.imported_articles = imported_count

    # Re-imported existing articles are stored here because your model
    # currently has no separate updated_articles field.
    guide_version.skipped_articles = updated_count

    guide_version.failed_articles = failed_count
    guide_version.import_log = "\n".join(logs)
    guide_version.completed_at = timezone.now()

    guide_version.save(
        update_fields=[
            "status",
            "total_articles",
            "imported_articles",
            "skipped_articles",
            "failed_articles",
            "import_log",
            "completed_at",
        ]
    )

    return {
        "total": len(parsed_articles),
        "imported": imported_count,
        "updated": updated_count,
        "skipped": updated_count,
        "failed": failed_count,
        "images": image_count,
        "logs": logs,
    }