from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from typing import List, Optional
import tempfile
import os
from datetime import datetime

from app.utils.auth import verify_token
from app.services.document_service import DocumentService
from app.services.drive_service import GoogleDriveService
from app.services.ai_analysis_service import DocumentAnalysisService
from app.models.document import DocumentCreate, DocumentUpdate, DocumentResponse

router = APIRouter()

@router.get("/", response_model=List[DocumentResponse])
async def get_documents(user_token: dict = Depends(verify_token)):
    """Obtener todos los documentos del usuario autenticado"""
    try:
        document_service = DocumentService()
        documents = await document_service.get_user_documents(user_token['uid'])
        return documents
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    user_token: dict = Depends(verify_token)
):
    """Obtener documento específico por ID"""
    try:
        document_service = DocumentService()
        document = await document_service.get_document_by_id(document_id, user_token['uid'])
        
        if document:
            return document
        else:
            raise HTTPException(status_code=404, detail="Documento no encontrado")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=DocumentResponse)
async def create_document(
    document_data: DocumentCreate,
    user_token: dict = Depends(verify_token)
):
    """Crear nuevo documento"""
    try:
        document_service = DocumentService()
        document = await document_service.create_document(user_token['uid'], document_data)
        return document
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload")
async def upload_and_analyze_document(
    file: UploadFile = File(...),
    user_token: dict = Depends(verify_token)
):
    """Subir archivo, analizarlo automáticamente y guardarlo en Google Drive con clasificación"""
    try:
        # Verificar tipo de archivo
        if not file.filename:
            raise HTTPException(status_code=400, detail="Nombre de archivo requerido")
        
        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Analizar documento con AI
            ai_service = DocumentAnalysisService()
            analysis = await ai_service.analyze_document(
                content, 
                file.content_type or "application/octet-stream",
                file.filename
            )
            
            # Obtener credenciales de Google Drive del usuario
            from app.services.oauth_service import GoogleOAuthService
            
            oauth_service = GoogleOAuthService()
            user_credentials = await oauth_service.refresh_user_tokens(user_token['uid'])
            
            if not user_credentials:
                raise HTTPException(
                    status_code=401, 
                    detail="Usuario no ha autorizado acceso a Google Drive. Use /api/v1/auth/google/authorize primero."
                )
            
            # Crear carpeta en Google Drive según categoría
            drive_service = GoogleDriveService(user_credentials)
            
            # Crear estructura de carpetas
            category_folder = await drive_service.get_or_create_folder(analysis['suggested_category'])
            
            # Subir archivo a Google Drive
            drive_file_id = await drive_service.upload_file(
                temp_file_path,
                file.filename,
                category_folder,
                file.content_type
            )
            
            # Crear documento en Firestore
            document_service = DocumentService()
            
            document_data = DocumentCreate(
                name=file.filename,
                category=analysis['suggested_category'],
                description=f"Documento analizado automáticamente. Categoría sugerida: {analysis['suggested_category']}",
                file_url=f"https://drive.google.com/file/d/{drive_file_id}/view",
                file_name=file.filename,
                file_size=len(content),
                file_type=file.content_type,
                expiry_date=analysis.get('expiry_date'),
                metadata=analysis.get('metadata', {}),
                tags=analysis.get('tags', [])
            )
            
            document = await document_service.create_document(user_token['uid'], document_data)
            
            # Limpiar archivo temporal
            os.unlink(temp_file_path)
            
            return {
                "message": "Documento subido y analizado exitosamente",
                "document": document,
                "analysis": analysis,
                "drive_file_id": drive_file_id,
                "drive_url": f"https://drive.google.com/file/d/{drive_file_id}/view"
            }
            
        except Exception as e:
            # Limpiar archivo temporal en caso de error
            os.unlink(temp_file_path)
            raise e
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: str,
    document_data: DocumentUpdate,
    user_token: dict = Depends(verify_token)
):
    """Actualizar documento existente"""
    try:
        document_service = DocumentService()
        document = await document_service.update_document(document_id, user_token['uid'], document_data)
        
        if document:
            return document
        else:
            raise HTTPException(status_code=404, detail="Documento no encontrado")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    user_token: dict = Depends(verify_token)
):
    """Eliminar documento"""
    try:
        document_service = DocumentService()
        success = await document_service.delete_document(document_id, user_token['uid'])
        
        if success:
            return {"message": "Documento eliminado correctamente", "document_id": document_id}
        else:
            raise HTTPException(status_code=404, detail="Documento no encontrado")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/categories/list")
async def get_document_categories(user_token: dict = Depends(verify_token)):
    """Obtener todas las categorías de documentos del usuario"""
    try:
        document_service = DocumentService()
        categories = await document_service.get_document_categories(user_token['uid'])
        return {"categories": categories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/expiring/list", response_model=List[DocumentResponse])
async def get_expiring_documents(
    days: int = Query(30, description="Días para considerar como 'por vencer'"),
    user_token: dict = Depends(verify_token)
):
    """Obtener documentos que vencen pronto"""
    try:
        document_service = DocumentService()
        documents = await document_service.get_expiring_documents(user_token['uid'], days)
        return documents
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/list", response_model=List[DocumentResponse])
async def search_documents(
    q: str = Query(..., description="Término de búsqueda"),
    user_token: dict = Depends(verify_token)
):
    """Buscar documentos por texto"""
    try:
        document_service = DocumentService()
        documents = await document_service.search_documents(user_token['uid'], q)
        return documents
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/drive/structure")
async def get_drive_folder_structure(user_token: dict = Depends(verify_token)):
    """Obtener estructura de carpetas de Google Drive"""
    try:
        # Obtener credenciales del usuario
        from app.services.oauth_service import GoogleOAuthService
        
        oauth_service = GoogleOAuthService()
        user_credentials = await oauth_service.refresh_user_tokens(user_token['uid'])
        
        if not user_credentials:
            raise HTTPException(
                status_code=401, 
                detail="Usuario no ha autorizado acceso a Google Drive. Use /api/v1/auth/google/authorize primero."
            )
        
        # Obtener estructura real de Google Drive
        drive_service = GoogleDriveService(user_credentials)
        folders = await drive_service.get_folder_structure()
        
        # Contar archivos en cada carpeta
        for folder in folders:
            files = await drive_service.get_files_in_folder(folder['id'])
            folder['files_count'] = len(files)
        
        return {"folders": folders}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
