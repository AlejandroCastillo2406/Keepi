#!/usr/bin/env python3
"""
Archivo de entrada principal para la aplicación Keepi API refactorizada
"""

import uvicorn
from app.main import app
from app.config.settings import settings

if __name__ == "__main__":
    print("🚀 Iniciando Keepi API...")
    print(f"📡 Servidor: {settings.host}:{settings.port}")
    print(f"🔧 Modo debug: {settings.debug}")
    print(f"📚 Documentación: http://{settings.host}:{settings.port}/docs")
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )
