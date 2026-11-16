"""Download the public Bird-MixIT four-source checkpoint."""

import base64
import hashlib
import urllib.request
from collections.abc import Callable
from pathlib import Path


MODEL_URL = (
    "https://storage.googleapis.com/gresearch/sound_separation/"
    "bird_mixit_model_checkpoints/output_sources4"
)
MODEL_FILES = (
    ("inference.meta", 3_194_589, "xE9Yjp2eRuRGaxsbhmyRAg=="),
    (
        "model.ckpt-3223090.data-00000-of-00001",
        110_260_324,
        "qeSqPX3VuQHudd9RDNngzg==",
    ),
    ("model.ckpt-3223090.index", 17_670, "4XMk2pI1CTruoBdNAFQ7Ww=="),
)
CHECKPOINT_PREFIX = "model.ckpt-3223090"


def _file_matches(path: Path, expected_size: int, expected_md5: str) -> bool:
    if not path.is_file() or path.stat().st_size != expected_size:
        return False
    digest = hashlib.md5(path.read_bytes()).digest()
    return base64.b64encode(digest).decode("ascii") == expected_md5


def model_is_ready(model_dir: str | Path) -> bool:
    directory = Path(model_dir)
    return all(
        _file_matches(directory / filename, size, checksum)
        for filename, size, checksum in MODEL_FILES
    )


def download_model(
    model_dir: str | Path,
    progress_callback: Callable[[int, int, str], None] | None = None,
) -> Path:
    """Download and verify the official model files, reporting total progress."""
    directory = Path(model_dir)
    directory.mkdir(parents=True, exist_ok=True)
    total_size = sum(size for _, size, _ in MODEL_FILES)
    completed_size = sum(
        size
        for filename, size, checksum in MODEL_FILES
        if _file_matches(directory / filename, size, checksum)
    )

    for filename, expected_size, expected_md5 in MODEL_FILES:
        destination = directory / filename
        if _file_matches(destination, expected_size, expected_md5):
            continue

        partial_path = destination.with_suffix(destination.suffix + ".part")
        request = urllib.request.Request(
            f"{MODEL_URL}/{filename}",
            headers={"User-Agent": "Kvitter-Bird-MixIT/1.0"},
        )
        downloaded_size = 0
        digest = hashlib.md5()
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                with partial_path.open("wb") as output_file:
                    while chunk := response.read(1024 * 1024):
                        output_file.write(chunk)
                        digest.update(chunk)
                        downloaded_size += len(chunk)
                        if progress_callback is not None:
                            progress_callback(
                                completed_size + downloaded_size,
                                total_size,
                                filename,
                            )
            actual_md5 = base64.b64encode(digest.digest()).decode("ascii")
            if downloaded_size != expected_size or actual_md5 != expected_md5:
                raise ValueError(f"Kontrollsumman stämmer inte för {filename}.")
            partial_path.replace(destination)
            completed_size += expected_size
        except Exception:
            partial_path.unlink(missing_ok=True)
            raise

    return directory