"""
Development server startup script with auto-reload
This script starts the FastAPI server with hot-reloading enabled.
Any changes to Python files will automatically restart the server.
"""
import uvicorn
import sys

if __name__ == "__main__":
    print("=" * 60)
    print("Starting Development Server with Auto-Reload")
    print("=" * 60)
    print("\nFeatures enabled:")
    print("  ✓ Auto-reload on code changes")
    print("  ✓ Hot-reloading enabled")
    print("  ✓ Debug mode active")
    print("\nServer Information:")
    print("  • API URL: http://localhost:8000")
    print("  • API Docs: http://localhost:8000/docs")
    print("  • ReDoc: http://localhost:8000/redoc")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60)
    print()

    try:
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            reload_delay=0.5,  # Delay before reloading after detecting changes
            log_level="info",
            access_log=True,
        )
    except KeyboardInterrupt:
        print("\n\nServer stopped by user")
        sys.exit(0)
