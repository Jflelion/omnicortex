from pathlib import Path
import sys

import uvicorn


PROJECT_ROOT = Path(__file__).resolve().parent
ENV_FILE = PROJECT_ROOT / ".env"
APP_MAIN_FILE = PROJECT_ROOT / "app" / "main.py"


def validate_project() -> None:
    """
    Validate the minimum files required to start OmniCortex.

    Raises:
        RuntimeError: If the application entry point or environment file
            cannot be found.
    """

    if not APP_MAIN_FILE.exists():
        raise RuntimeError(
            f"FastAPI entry point not found: {APP_MAIN_FILE}"
        )

    if not ENV_FILE.exists():
        raise RuntimeError(
            f"Environment file not found: {ENV_FILE}"
        )


def main() -> None:
    """
    Start the OmniCortex development server.
    """

    try:
        validate_project()
    except RuntimeError as error:
        print()
        print("OmniCortex could not start.")
        print(error)
        print()
        sys.exit(1)

    print()
    print("OmniCortex")
    print("────────────────────────────────────────")
    print(f"Project: {PROJECT_ROOT}")
    print("Environment: development")
    print("API: http://127.0.0.1:8000")
    print("Swagger: http://127.0.0.1:8000/docs")
    print("Reload: enabled")
    print("────────────────────────────────────────")
    print()

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        app_dir=str(PROJECT_ROOT),
        log_level="info",
    )


if __name__ == "__main__":
    main()