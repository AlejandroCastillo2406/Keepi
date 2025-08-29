from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any

from app.utils.auth import verify_token
from app.services.oauth_service import GoogleOAuthService

router = APIRouter()

@router.get("/verify")
async def verify_authentication(user_token: dict = Depends(verify_token)):
    """Verificar token de autenticación"""
    return {
        "authenticated": True,
        "user_id": user_token['uid'],
        "email": user_token['email']
    }

@router.get("/current-user")
async def get_current_user(user_token: dict = Depends(verify_token)):
    """Obtener información del usuario actual"""
    try:
        from app.services.user_service import UserService
        
        user_service = UserService()
        user = await user_service.get_user_by_id(user_token['uid'])
        
        if user:
            return user
        else:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/google/authorize")
async def authorize_google_drive(user_token: dict = Depends(verify_token)):
    """Generar URL de autorización para Google Drive"""
    try:
        oauth_service = GoogleOAuthService()
        auth_data = await oauth_service.get_authorization_url(user_token['uid'])
        
        return {
            "message": "URL de autorización generada",
            "authorization_url": auth_data["authorization_url"],
            "state": auth_data["state"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/google/callback")
async def google_oauth_callback(
    code: str = Query(..., description="Código de autorización"),
    state: str = Query(None, description="Estado de la autorización")
):
    """Callback de OAuth2 para Google Drive - NO requiere autenticación"""
    try:
        oauth_service = GoogleOAuthService()
        tokens = await oauth_service.exchange_code_for_tokens(code, state)
        
        return {
            "message": "Autorización exitosa",
            "access_granted": True,
            "user_id": tokens["user_id"],
            "scopes": tokens["scopes"],
            "expires_at": tokens["expires_at"]
        }
        
    except Exception as e:
        print(f"Error en callback de Google OAuth: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/google/status")
async def check_google_drive_status(user_token: dict = Depends(verify_token)):
    """Verificar estado de autorización con Google Drive"""
    try:
        oauth_service = GoogleOAuthService()
        status = await oauth_service.check_user_drive_access(user_token['uid'])
        
        return status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/google/revoke")
async def revoke_google_drive_access(user_token: dict = Depends(verify_token)):
    """Revocar acceso a Google Drive"""
    try:
        oauth_service = GoogleOAuthService()
        success = await oauth_service.revoke_user_access(user_token['uid'])
        
        if success:
            return {
                "message": "Acceso a Google Drive revocado exitosamente",
                "access_revoked": True
            }
        else:
            raise HTTPException(status_code=500, detail="Error revocando acceso")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
