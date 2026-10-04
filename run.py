"""
DevPulse - Application Launcher
"""
import os
import uvicorn

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    host = os.getenv("HOST", "0.0.0.0")
    print(f"🚀 Iniciando DevPulse en http://{host}:{port} ...")
    uvicorn.run("devpulse.main:app", host=host, port=port, reload=False)
