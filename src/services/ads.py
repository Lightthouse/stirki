"""Рекламные картинки: файлы в `advertising/`, список и модерация — в таблице `ads`.

Папка `advertising/` в Docker подключена томом (compose.yml), поэтому картинки,
загруженные через админку, видны сразу и переживают пересборку образа.
"""
import re
import secrets
from pathlib import Path

ADS_DIR = Path("advertising")
ADS_URL_PREFIX = "/advertising/"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_FILE_SIZE = 5 * 1024 * 1024


class AdUploadError(ValueError):
    """Файл не подходит для загрузки — текст ошибки показывается в админке."""


def save_ad_file(filename: str, content: bytes) -> str:
    """Сохраняет картинку и возвращает её путь для сайта (`/advertising/a3f9-имя.jpg`).

    Случайный префикс делает путь уникальным: статистика просмотров (`ad_views`)
    считается по пути, и новая картинка с тем же именем не смешается со старой.
    """
    original = Path(filename or "").name
    ext = Path(original).suffix.lower()
    if not content:
        raise AdUploadError("Выберите файл картинки")
    if ext not in ALLOWED_EXTENSIONS:
        raise AdUploadError(f"Допустимые форматы: {', '.join(sorted(ALLOWED_EXTENSIONS))}")
    if len(content) > MAX_FILE_SIZE:
        raise AdUploadError(f"Файл больше {MAX_FILE_SIZE // 1024 // 1024} МБ")

    stem = re.sub(r"[^\w.-]+", "_", Path(original).stem).strip("._")[:60] or "ad"
    name = f"{secrets.token_hex(2)}-{stem}{ext}"
    ADS_DIR.mkdir(exist_ok=True)
    (ADS_DIR / name).write_bytes(content)
    return ADS_URL_PREFIX + name


def delete_ad_file(image_path: str) -> None:
    """Удаляет файл картинки. Статистика просмотров в `ad_views` остаётся."""
    name = Path(image_path.removeprefix(ADS_URL_PREFIX)).name
    (ADS_DIR / name).unlink(missing_ok=True)
