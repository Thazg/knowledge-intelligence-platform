from backend.ingestion.models import DocumentFile

VALID_EXTENSIONS = {
    ".md",
    ".mdx",
    ".rst",
    ".html",
    ".txt",
}

IGNORED_FILES = {
    "README.md",
    "LICENSE",
    "NOTICE",
    "CODEOWNERS",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "CLAUDE.md",
    "AGENTS.md",
}

IGNORED_DIRECTORIES = {
    ".agents",
    ".github",
    ".git",
    ".vscode",
    "_build",
    "_vendor",
    "_vale",
    "api-ref-assets",
    "api-ref-generator",
    "archetypes",
    "assets",
    "generated",
    "hack",
    "i18n",
    "layouts",
    "node_modules",
    "scripts",
    "static",
    "themes",
    "update-imported-docs",
}

TRANSLATION_ROOTS = {
    "ar",
    "bn",
    "de",
    "es",
    "fa",
    "fr",
    "hi",
    "id",
    "it",
    "ja",
    "ko",
    "pl",
    "pt",
    "pt-br",
    "ro",
    "ru",
    "tr",
    "uk",
    "vi",
    "zh",
    "zh-cn",
    "zh-hant",
}

IGNORED_PATH_PARTS = (
    "generated",
    "_build",
)


class DocumentFilter:

    def is_valid(
        self,
        document: DocumentFile,
    ) -> bool:

        if document.extension not in VALID_EXTENSIONS:
            return False

        if document.filename in IGNORED_FILES:
            return False

        parts = tuple(
            part.lower()
            for part in document.relative_path.parts
        )

        if any(part in IGNORED_DIRECTORIES for part in parts):
            return False

        if any(part in IGNORED_PATH_PARTS for part in parts):
            return False

        if document.source == "fastapi":
            if parts and parts[0] in TRANSLATION_ROOTS:
                return False

        if document.source == "huggingface":
            if len(parts) >= 2 and parts[0] == "source" and parts[1] != "en":
                return False

        if document.source == "kubernetes":
            if len(parts) >= 2 and parts[0] == "content" and parts[1] != "en":
                return False

            if (
                len(parts) >= 3
                and parts[:2] == ("content", "en")
                and parts[2] != "docs"
            ):
                return False

        return True
