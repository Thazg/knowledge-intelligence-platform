import os
import shutil
import stat
import subprocess
import tarfile
from pathlib import Path

from git import GitCommandError, Repo

from backend.ingestion.config import DOCUMENT_SOURCES

BASE_DIR = Path(__file__).resolve().parents[2]

RAW_DATA_DIR = BASE_DIR / "data" / "raw"
TEMP_DATA_DIR = BASE_DIR / "data" / "temp"


def _on_rm_error(func, path, exc_info):
    """
    Handle read-only files on Windows.
    """
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception as e:
        print(f"[ERROR] Failed to remove {path}: {e}")


def clone_and_extract(name: str, config: dict) -> None:
    temp_dir = TEMP_DATA_DIR / name
    output_dir = RAW_DATA_DIR / name

    if output_dir.exists():
        print(f"[SKIP] {name}")
        return

    print(f"[CLONE] {name}")

    if temp_dir.exists():
        shutil.rmtree(temp_dir, onerror=_on_rm_error)

    TEMP_DATA_DIR.mkdir(parents=True, exist_ok=True)

    try:
        Repo.clone_from(
            config["repo"],
            temp_dir,
            depth=1,
        )

    except GitCommandError as e:
        print(f"[WARN] Clone with checkout failed for {name}: {e}")
        print(f"[INFO] Attempting bare clone and archive extraction for {name}")

        if temp_dir.exists():
            shutil.rmtree(temp_dir, onerror=_on_rm_error)

        try:
            Repo.clone_from(
                config["repo"],
                temp_dir,
                bare=True,
                depth=1,
            )
        except Exception as e:
            print(f"[ERROR] Bare clone failed: {e}")
            return

        archive_path = TEMP_DATA_DIR / f"{name}.tar"
        extract_dir = TEMP_DATA_DIR / f"{name}_archive"

        docs_path = config["docs_path"]
        treeish = "HEAD" if docs_path == "." else f"HEAD:{docs_path}"

        try:
            subprocess.run(
                [
                    "git",
                    "--git-dir",
                    str(temp_dir),
                    "archive",
                    "--format=tar",
                    "-o",
                    str(archive_path),
                    treeish,
                ],
                check=True,
            )

            extract_dir.mkdir(parents=True, exist_ok=True)

            with tarfile.open(archive_path) as tar:
                def is_safe(member):
                    if member.name.startswith("/"):
                        return False

                    parts = Path(member.name).parts

                    if ".." in parts:
                        return False

                    forbidden = set('<>:"\\|?*')

                    for part in parts:
                        if part.endswith(" ") or part.endswith("."):
                            return False

                        if any(c in forbidden for c in part):
                            return False

                    return True

                members = [m for m in tar.getmembers() if is_safe(m)]

                tar.extractall(extract_dir, members=members)

            roots = list(extract_dir.iterdir())

            if len(roots) == 1 and roots[0].is_dir():
                extracted_root = roots[0]
            else:
                extracted_root = extract_dir

            docs_source = extracted_root

            if not docs_source.exists():
                print(f"[WARN] docs path not found: {docs_source}")
                return

            print(f"[COPY] {name}")

            shutil.copytree(
                docs_source,
                output_dir,
                dirs_exist_ok=True,
                ignore=shutil.ignore_patterns(".git"),
            )

        finally:
            if archive_path.exists():
                archive_path.unlink()

            if extract_dir.exists():
                shutil.rmtree(extract_dir, onerror=_on_rm_error)

            if temp_dir.exists():
                shutil.rmtree(temp_dir, onerror=_on_rm_error)

        print(f"[DONE] {name}")
        return

    docs_source = temp_dir / config["docs_path"]

    if not docs_source.exists():
        print(f"[WARN] docs path not found: {docs_source}")

        if temp_dir.exists():
            shutil.rmtree(temp_dir, onerror=_on_rm_error)

        return

    print(f"[COPY] {name}")

    shutil.copytree(
        docs_source,
        output_dir,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns(".git"),
    )

    print(f"[CLEAN] {name}")

    shutil.rmtree(temp_dir, onerror=_on_rm_error)

    print(f"[DONE] {name}")


def main() -> None:
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    for name, config in DOCUMENT_SOURCES.items():
        clone_and_extract(name, config)
