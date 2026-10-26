# Contributing

Thanks for helping improve Enterprise KIP. Please open an issue before a large behavior change so the scope and evidence can be discussed.

## Development

Use CPython 3.13 for the backend and Node.js 20.9+ for the web app. See the [README](README.md#quick-start) and [reproducibility guide](docs/06_reproducibility_and_operations.md) for setup and profile-specific requirements.

Before opening a pull request, run the checks relevant to your change:

```bash
ruff check .
pytest tests/ -q -m "not integration"
cd web
npm ci
npm run lint
npm test
npx tsc --noEmit
npm run build
```

Retrieval or generation changes should include the affected evaluation cases, the prior baseline, the evaluation conditions, and a link to the resulting report. Keep local corpus copies, credentials, model downloads, and generated logs out of commits. Use a focused branch and describe the user-visible change, validation, and remaining limitations in the pull request.

The project includes third-party documentation in its indexed corpus. Contributions must respect upstream content and dependency licenses; see the [dataset guide](data/README.md) and [MIT License](LICENSE).
