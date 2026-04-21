#!/usr/bin/env python3
"""
Script de démarrage pour développement local.
FF SIGNALS MINI - Backend
"""
import sys
import os
import subprocess
import importlib.util
from pathlib import Path

def check_dependencies() -> bool:
    """Vérifie et installe les dépendances manquantes."""
    required = [
        "fastapi", "uvicorn", "pydantic", "numpy",
        "yfinance", "aiohttp", "websockets", "aiosqlite"
    ]
    missing = []
    for pkg in required:
        if importlib.util.find_spec(pkg) is None:
            missing.append(pkg)
    
    if missing:
        print(f"⚠️  Dépendances manquantes : {', '.join(missing)}")
        print("📦 Installation automatique...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        return False
    return True

def setup_directories() -> None:
    """Crée les dossiers nécessaires."""
    Path("data").mkdir(exist_ok=True)
    Path("logs").mkdir(exist_ok=True)

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 FF SIGNALS MINI - Backend")
    print(f"🐍 Python {sys.version.split()[0]}")
    print("=" * 60)
    
    setup_directories()
    check_dependencies()
    
    import uvicorn
    
    port = int(os.environ.get("PORT", 8000))
    
    print(f"📡 Démarrage sur http://localhost:{port}")
    print(f"📚 Documentation: http://localhost:{port}/docs")
    print("=" * 60)
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info",
    )