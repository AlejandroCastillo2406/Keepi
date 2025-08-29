from typing import Optional, List, Dict, Any
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from googleapiclient.errors import HttpError
import io
import os
from datetime import datetime

class GoogleDriveService:
    """Servicio para integración con Google Drive"""
    
    def __init__(self, credentials: Credentials):
        self.credentials = credentials
        self.service = build('drive', 'v3', credentials=credentials)
        self.folders_cache = {}
    
    async def create_folder(self, name: str, parent_id: Optional[str] = None) -> str:
        """Crear carpeta en Google Drive"""
        try:
            folder_metadata = {
                'name': name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            if parent_id:
                folder_metadata['parents'] = [parent_id]
            
            folder = self.service.files().create(
                body=folder_metadata,
                fields='id'
            ).execute()
            
            folder_id = folder.get('id')
            self.folders_cache[name] = folder_id
            return folder_id
            
        except HttpError as error:
            print(f'Error creando carpeta: {error}')
            raise
    
    async def get_or_create_folder(self, name: str, parent_id: Optional[str] = None) -> str:
        """Obtener carpeta existente o crear nueva"""
        # Buscar en caché primero
        if name in self.folders_cache:
            return self.folders_cache[name]
        
        try:
            # Buscar carpeta existente
            query = f"name='{name}' and mimeType='application/vnd.google-apps.folder'"
            if parent_id:
                query += f" and '{parent_id}' in parents"
            
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            
            files = results.get('files', [])
            
            if files:
                folder_id = files[0]['id']
                self.folders_cache[name] = folder_id
                return folder_id
            else:
                # Crear nueva carpeta
                return await self.create_folder(name, parent_id)
                
        except HttpError as error:
            print(f'Error buscando/creando carpeta: {error}')
            raise
    
    async def upload_file(self, file_path: str, file_name: str, folder_id: str, 
                         mime_type: Optional[str] = None) -> str:
        """Subir archivo a Google Drive"""
        try:
            if not mime_type:
                mime_type = 'application/octet-stream'
            
            file_metadata = {
                'name': file_name,
                'parents': [folder_id]
            }
            
            media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, size, mimeType, createdTime'
            ).execute()
            
            return file.get('id')
            
        except HttpError as error:
            print(f'Error subiendo archivo: {error}')
            raise
    
    async def get_folder_structure(self, folder_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtener estructura de carpetas"""
        try:
            query = "mimeType='application/vnd.google-apps.folder'"
            if folder_id:
                query += f" and '{folder_id}' in parents"
            else:
                query += " and 'root' in parents"
            
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name, createdTime, modifiedTime)',
                orderBy='name'
            ).execute()
            
            folders = []
            for folder in results.get('files', []):
                folders.append({
                    'id': folder['id'],
                    'name': folder['name'],
                    'created_time': folder.get('createdTime'),
                    'modified_time': folder.get('modifiedTime')
                })
            
            return folders
            
        except HttpError as error:
            print(f'Error obteniendo estructura de carpetas: {error}')
            raise
    
    async def get_files_in_folder(self, folder_id: str) -> List[Dict[str, Any]]:
        """Obtener archivos en una carpeta específica"""
        try:
            results = self.service.files().list(
                q=f"'{folder_id}' in parents and mimeType!='application/vnd.google-apps.folder'",
                spaces='drive',
                fields='files(id, name, size, mimeType, createdTime, modifiedTime)',
                orderBy='name'
            ).execute()
            
            files = []
            for file in results.get('files', []):
                files.append({
                    'id': file['id'],
                    'name': file['name'],
                    'size': file.get('size'),
                    'mime_type': file.get('mimeType'),
                    'created_time': file.get('createdTime'),
                    'modified_time': file.get('modifiedTime')
                })
            
            return files
            
        except HttpError as error:
            print(f'Error obteniendo archivos: {error}')
            raise
    
    async def delete_file(self, file_id: str) -> bool:
        """Eliminar archivo de Google Drive"""
        try:
            self.service.files().delete(fileId=file_id).execute()
            return True
        except HttpError as error:
            print(f'Error eliminando archivo: {error}')
            return False
    
    async def get_file_download_url(self, file_id: str) -> str:
        """Obtener URL de descarga del archivo"""
        try:
            file = self.service.files().get(
                fileId=file_id,
                fields='webViewLink, webContentLink'
            ).execute()
            
            return file.get('webContentLink', '')
            
        except HttpError as error:
            print(f'Error obteniendo URL de descarga: {error}')
            return ''
