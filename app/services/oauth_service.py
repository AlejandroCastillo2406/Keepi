from typing import Dict, Any, Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
import json
import os
from datetime import datetime, timedelta
from app.config.settings import settings

class GoogleOAuthService:
    """Servicio para manejar autenticación OAuth2 con Google"""
    
    def __init__(self):
        # Configuración OAuth2 desde variables de entorno
        self.client_secrets_file = settings.google_client_secrets_path
        self.scopes = [
            'openid',
            'https://www.googleapis.com/auth/drive.file',
            'https://www.googleapis.com/auth/drive.metadata.readonly',
            'https://www.googleapis.com/auth/userinfo.email'
        ]
        # URL de callback desde variables de entorno
        self.redirect_uri = settings.google_redirect_uri or f"{settings.host}/api/v1/auth/google/callback"
    
    async def get_authorization_url(self, user_id: str) -> Dict[str, str]:
        """Generar URL de autorización para Google Drive"""
        try:
            flow = Flow.from_client_secrets_file(
                self.client_secrets_file,
                scopes=self.scopes,
                redirect_uri=self.redirect_uri
            )
            
            # Agregar estado para identificar al usuario
            flow.state = json.dumps({"user_id": user_id})
            
            authorization_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'
            )
            
            return {
                "authorization_url": authorization_url,
                "state": state
            }
            
        except Exception as e:
            print(f"Error generando URL de autorización: {e}")
            raise
    
    async def exchange_code_for_tokens(self, authorization_code: str, user_id: str) -> Dict[str, Any]:
        """Intercambiar código de autorización por tokens"""
        try:
            # Crear nuevo flow para intercambiar tokens
            flow = Flow.from_client_secrets_file(
                self.client_secrets_file,
                scopes=self.scopes,
                redirect_uri=self.redirect_uri
            )
            
            # Intercambiar código por tokens
            flow.fetch_token(code=authorization_code)
            
            credentials = flow.credentials
            
            # Usar el user_id que se pasa como parámetro
            if not user_id:
                user_id = "default_user"
                print("⚠️ Usando user_id por defecto para testing")
            
            print(f"✅ Guardando credenciales para usuario: {user_id}")
            
            # Guardar credenciales en Firestore
            await self._save_user_credentials(user_id, credentials)
            
            return {
                "access_token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "expires_at": credentials.expiry.isoformat() if credentials.expiry else None,
                "scopes": credentials.scopes,
                "user_id": user_id
            }
            
        except Exception as e:
            print(f"Error intercambiando código por tokens: {e}")
            raise
    
    async def refresh_user_tokens(self, user_id: str) -> Optional[Credentials]:
        """Refrescar tokens del usuario"""
        try:
            # Obtener credenciales guardadas
            credentials_data = await self._get_user_credentials(user_id)
            
            if not credentials_data:
                return None
            
            credentials = Credentials(
                token=credentials_data.get('access_token'),
                refresh_token=credentials_data.get('refresh_token'),
                token_uri="https://oauth2.googleapis.com/token",
                client_id=credentials_data.get('client_id'),
                client_secret=credentials_data.get('client_secret'),
                scopes=credentials_data.get('scopes', self.scopes)
            )
            
            # Refrescar si es necesario
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                
                # Actualizar tokens en Firestore
                await self._update_user_credentials(user_id, credentials)
            
            return credentials
            
        except Exception as e:
            print(f"Error refrescando tokens: {e}")
            return None
    
    async def revoke_user_access(self, user_id: str) -> bool:
        """Revocar acceso del usuario a Google Drive"""
        try:
            # Eliminar credenciales de Firestore
            await self._delete_user_credentials(user_id)
            return True
            
        except Exception as e:
            print(f"Error revocando acceso: {e}")
            return False
    
    async def check_user_drive_access(self, user_id: str) -> Dict[str, Any]:
        """Verificar si el usuario tiene acceso a Google Drive"""
        try:
            credentials_data = await self._get_user_credentials(user_id)
            
            if not credentials_data:
                return {
                    "has_access": False,
                    "message": "Usuario no ha autorizado acceso a Google Drive"
                }
            
            # Verificar si el token ha expirado
            expires_at = credentials_data.get('expires_at')
            if expires_at:
                expiry_time = datetime.fromisoformat(expires_at)
                if datetime.now() > expiry_time:
                    return {
                        "has_access": False,
                        "message": "Token expirado, requiere renovación"
                    }
            
            return {
                "has_access": True,
                "message": "Usuario tiene acceso activo a Google Drive",
                "scopes": credentials_data.get('scopes', []),
                "expires_at": expires_at
            }
            
        except Exception as e:
            print(f"Error verificando acceso: {e}")
            return {
                "has_access": False,
                "message": f"Error verificando acceso: {str(e)}"
            }
    
    async def _save_user_credentials(self, user_id: str, credentials: Credentials) -> bool:
        """Guardar credenciales del usuario en Firestore"""
        try:
            from app.config.database import DatabaseConfig
            
            db = DatabaseConfig.get_firestore_client()
            
            credentials_data = {
                'user_id': user_id,
                'access_token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'expires_at': credentials.expiry.isoformat() if credentials.expiry else None,
                'scopes': credentials.scopes,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'token_uri': credentials.token_uri,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # Guardar en colección de credenciales OAuth
            db.collection('oauth_credentials').document(user_id).set(credentials_data)
            print(f"✅ Credenciales guardadas para usuario: {user_id}")
            return True
            
        except Exception as e:
            print(f"Error guardando credenciales: {e}")
            return False
    
    async def _get_user_credentials(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Obtener credenciales del usuario desde Firestore"""
        try:
            from app.config.database import DatabaseConfig
            
            db = DatabaseConfig.get_firestore_client()
            
            doc = db.collection('oauth_credentials').document(user_id).get()
            
            if doc.exists:
                return doc.to_dict()
            return None
            
        except Exception as e:
            print(f"Error obteniendo credenciales: {e}")
            return None
    
    async def _update_user_credentials(self, user_id: str, credentials: Credentials) -> bool:
        """Actualizar credenciales del usuario en Firestore"""
        try:
            from app.config.database import DatabaseConfig
            
            db = DatabaseConfig.get_firestore_client()
            
            update_data = {
                'access_token': credentials.token,
                'expires_at': credentials.expiry.isoformat() if credentials.expiry else None,
                'updated_at': datetime.now().isoformat()
            }
            
            db.collection('oauth_credentials').document(user_id).update(update_data)
            return True
            
        except Exception as e:
            print(f"Error actualizando credenciales: {e}")
            return False
    
    async def _delete_user_credentials(self, user_id: str) -> bool:
        """Eliminar credenciales del usuario de Firestore"""
        try:
            from app.config.database import DatabaseConfig
            
            db = DatabaseConfig.get_firestore_client()
            
            db.collection('oauth_credentials').document(user_id).delete()
            return True
            
        except Exception as e:
            print(f"Error eliminando credenciales: {e}")
            return False
