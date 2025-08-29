#!/usr/bin/env python3
"""
Script inteligente para crear colecciones y campos en Firestore
Revisa si existen y crea solo lo que falta
"""

import firebase_admin
from firebase_admin import credentials, firestore
import json
from datetime import datetime, timedelta
import os
import random
import string

# Configuración desde variables de entorno
cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "keepi-eff0f-280033bc5e27.json")

def initialize_firebase():
    """Inicializar Firebase Admin SDK"""
    try:
        # Verificar si ya está inicializado
        firebase_admin.get_app()
        print("✅ Firebase ya está inicializado")
    except ValueError:
        try:
            # Inicializar con credenciales de servicio
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            print(f"✅ Firebase inicializado con credenciales: {cred_path}")
        except Exception as e:
            print(f"❌ Error inicializando Firebase: {e}")
            raise
    
    return firestore.client()

def check_collection_exists(db, collection_name):
    """Verificar si una colección existe"""
    try:
        docs = db.collection(collection_name).limit(1).stream()
        return True
    except Exception:
        return False

def check_collection_has_documents(db, collection_name):
    """Verificar si una colección tiene documentos"""
    try:
        docs = list(db.collection(collection_name).limit(1).stream())
        return len(docs) > 0
    except Exception:
        return False

def check_document_exists(db, collection_name, doc_id):
    """Verificar si un documento existe"""
    try:
        doc = db.collection(collection_name).document(doc_id).get()
        return doc.exists
    except Exception:
        return False

def create_collection_with_sample_data(db, collection_name, sample_data):
    """Crear colección con documento de ejemplo"""
    try:
        # Crear documento de ejemplo
        doc_ref = db.collection(collection_name).document('sample_document')
        doc_ref.set(sample_data)
        print(f"✅ Colección '{collection_name}' actualizada con documento de ejemplo")
        return True
    except Exception as e:
        print(f"❌ Error creando documento en '{collection_name}': {e}")
        return False

def create_folders_collection(db):
    """Crear o actualizar colección de carpetas"""
    if check_collection_exists(db, 'folders'):
        if check_collection_has_documents(db, 'folders'):
            print("✅ Colección 'folders' ya existe con documentos")
            return True
        else:
            print("⚠️ Colección 'folders' existe pero está vacía - creando documento de ejemplo")
    else:
        print("📝 Creando nueva colección 'folders'")
    
    sample_folder = {
        'id': 'folder_sample_123',
        'user_id': 'test_user',
        'name': 'Carpeta de Ejemplo',
        'category': 'General',
        'description': 'Carpeta de ejemplo para la colección',
        'parent_folder_id': None,
        'drive_folder_id': 'google_drive_folder_id_example',
        'drive_parent_id': None,
        'color': '#4285F4',
        'icon': '📁',
        'documents_count': 0,
        'subfolders_count': 0,
        'is_archived': False,
        'is_favorite': False,
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    
    return create_collection_with_sample_data(db, 'folders', sample_folder)

def create_oauth_credentials_collection(db):
    """Crear o actualizar colección de credenciales OAuth"""
    if check_collection_exists(db, 'oauth_credentials'):
        if check_collection_has_documents(db, 'oauth_credentials'):
            print("✅ Colección 'oauth_credentials' ya existe con documentos")
            return True
        else:
            print("⚠️ Colección 'oauth_credentials' existe pero está vacía - creando documento de ejemplo")
    else:
        print("📝 Creando nueva colección 'oauth_credentials'")
    
    sample_credentials = {
        'user_id': 'test_user',
        'access_token': 'sample_access_token',
        'refresh_token': 'sample_refresh_token',
        'expires_at': datetime.now().isoformat(),
        'scopes': [
            'openid',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/drive.metadata.readonly',
            'https://www.googleapis.com/auth/drive.file'
        ],
        'client_id': 'sample_client_id.apps.googleusercontent.com',
        'client_secret': 'sample_client_secret',
        'token_uri': 'https://oauth2.googleapis.com/token',
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    
    return create_collection_with_sample_data(db, 'oauth_credentials', sample_credentials)

def create_ai_analysis_collection(db):
    """Crear o actualizar colección de análisis AI"""
    if check_collection_exists(db, 'ai_analysis'):
        if check_collection_has_documents(db, 'ai_analysis'):
            print("✅ Colección 'ai_analysis' ya existe con documentos")
            return True
        else:
            print("⚠️ Colección 'ai_analysis' existe pero está vacía - creando documento de ejemplo")
    else:
        print("📝 Creando nueva colección 'ai_analysis'")
    
    sample_analysis = {
        'id': 'analysis_sample_123',
        'user_id': 'test_user',
        'document_id': 'doc1',
        'suggested_category': 'General',
        'confidence_score': 0.8,
        'extracted_text': 'Texto extraído de ejemplo',
        'metadata': {
            'fechas_encontradas': [],
            'montos': [],
            'numeros_documento': []
        },
        'tags': ['ejemplo', 'general'],
        'expiry_date': None,
        'document_number': None,
        'organization': None,
        'processing_time_ms': 1000,
        'ai_model_version': '1.0.0',
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    
    return create_collection_with_sample_data(db, 'ai_analysis', sample_analysis)

def create_ai_analysis_history_collection(db):
    """Crear o actualizar colección de historial de análisis AI"""
    if check_collection_exists(db, 'ai_analysis_history'):
        if check_collection_has_documents(db, 'ai_analysis_history'):
            print("✅ Colección 'ai_analysis_history' ya existe con documentos")
            return True
        else:
            print("⚠️ Colección 'ai_analysis_history' existe pero está vacía - creando documento de ejemplo")
    else:
        print("📝 Creando nueva colección 'ai_analysis_history'")
    
    sample_history = {
        'id': 'history_sample_123',
        'document_id': 'doc1',
        'user_id': 'test_user',
        'analysis_version': 1,
        'previous_category': None,
        'new_category': 'General',
        'confidence_score': 0.8,
        'reason_for_change': 'Análisis inicial',
        'created_at': datetime.now().isoformat()
    }
    
    return create_collection_with_sample_data(db, 'ai_analysis_history', sample_history)

def create_audit_logs_collection(db):
    """Crear o actualizar colección de logs de auditoría"""
    if check_collection_exists(db, 'audit_logs'):
        if check_collection_has_documents(db, 'audit_logs'):
            print("✅ Colección 'audit_logs' ya existe con documentos")
            return True
        else:
            print("⚠️ Colección 'audit_logs' existe pero está vacía - creando documento de ejemplo")
    else:
        print("📝 Creando nueva colección 'audit_logs'")
    
    sample_audit = {
        'id': 'audit_sample_123',
        'user_id': 'test_user',
        'action_type': 'document_upload',
        'resource_type': 'document',
        'resource_id': 'doc1',
        'description': 'Usuario subió documento de ejemplo',
        'ip_address': os.getenv('DEFAULT_IP_ADDRESS', '127.0.0.1'),
        'user_agent': 'Script de ejemplo',
        'metadata': {
            'file_size': 1024,
            'file_type': 'application/pdf'
        },
        'success': True,
        'error_message': None,
        'created_at': datetime.now().isoformat()
    }
    
    return create_collection_with_sample_data(db, 'audit_logs', sample_audit)

def create_search_index_collection(db):
    """Crear o actualizar colección de índice de búsqueda"""
    if check_collection_exists(db, 'search_index'):
        if check_collection_has_documents(db, 'search_index'):
            print("✅ Colección 'search_index' ya existe con documentos")
            return True
        else:
            print("⚠️ Colección 'search_index' existe pero está vacía - creando documento de ejemplo")
    else:
        print("📝 Creando nueva colección 'search_index'")
    
    sample_search = {
        'id': 'search_sample_123',
        'document_id': 'doc1',
        'user_id': 'test_user',
        'content': 'Contenido de ejemplo para búsqueda',
        'title': 'Documento de Ejemplo',
        'category': 'General',
        'tags': ['ejemplo', 'general'],
        'metadata': {
            'fechas_encontradas': [],
            'montos': []
        },
        'file_type': 'application/pdf',
        'language': 'es',
        'search_vector': [0.1, 0.2, 0.3],
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    
    return create_collection_with_sample_data(db, 'search_index', sample_search)

def create_backup_sync_collection(db):
    """Crear o actualizar colección de respaldo y sincronización"""
    if check_collection_exists(db, 'backup_sync'):
        if check_collection_has_documents(db, 'backup_sync'):
            print("✅ Colección 'backup_sync' ya existe con documentos")
            return True
        else:
            print("⚠️ Colección 'backup_sync' existe pero está vacía - creando documento de ejemplo")
    else:
        print("📝 Creando nueva colección 'backup_sync'")
    
    sample_backup = {
        'id': 'backup_sample_123',
        'user_id': 'test_user',
        'sync_type': 'backup',
        'status': 'completed',
        'description': 'Respaldo de ejemplo',
        'source_paths': ['/documents', '/folders'],
        'destination_folder_id': 'google_drive_backup_folder',
        'include_deleted': False,
        'compression': True,
        'encryption': False,
        'progress_percentage': 100.0,
        'error_message': None,
        'started_at': datetime.now().isoformat(),
        'completed_at': datetime.now().isoformat(),
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    
    return create_collection_with_sample_data(db, 'backup_sync', sample_backup)

def create_sync_conflicts_collection(db):
    """Crear o actualizar colección de conflictos de sincronización"""
    if check_collection_exists(db, 'sync_conflicts'):
        if check_collection_has_documents(db, 'sync_conflicts'):
            print("✅ Colección 'sync_conflicts' ya existe con documentos")
            return True
        else:
            print("⚠️ Colección 'sync_conflicts' existe pero está vacía - creando documento de ejemplo")
    else:
        print("📝 Creando nueva colección 'sync_conflicts'")
    
    sample_conflict = {
        'id': 'conflict_sample_123',
        'backup_sync_id': 'backup_sample_123',
        'user_id': 'test_user',
        'file_path': '/documents/ejemplo.pdf',
        'conflict_type': 'modified',
        'local_version': {
            'modified_at': datetime.now().isoformat(),
            'size': 1024
        },
        'remote_version': {
            'modified_at': datetime.now().isoformat(),
            'size': 1024
        },
        'resolution': 'keep_local',
        'created_at': datetime.now().isoformat(),
        'resolved_at': datetime.now().isoformat()
    }
    
    return create_collection_with_sample_data(db, 'sync_conflicts', sample_conflict)

def main():
    """Función principal"""
    print("🚀 Iniciando creación inteligente de colecciones en Firestore...")
    print("=" * 60)
    print("📋 NOTA: Las colecciones 'users', 'documents' y 'notifications' ya existen")
    print("🔧 Se crearán documentos de ejemplo en las colecciones vacías")
    print("=" * 60)
    
    # Inicializar Firebase
    db = initialize_firebase()
    if not db:
        return
    
    print("\n📊 Verificando y actualizando colecciones...")
    print("-" * 40)
    
    # Lista de funciones para crear/actualizar colecciones
    collection_creators = [
        create_folders_collection,
        create_oauth_credentials_collection,
        create_ai_analysis_collection,
        create_ai_analysis_history_collection,
        create_audit_logs_collection,
        create_search_index_collection,
        create_backup_sync_collection,
        create_sync_conflicts_collection
    ]
    
    # Crear/actualizar colecciones
    success_count = 0
    total_count = len(collection_creators)
    
    for creator in collection_creators:
        try:
            if creator(db):
                success_count += 1
        except Exception as e:
            print(f"❌ Error en {creator.__name__}: {e}")
    
    print("\n" + "=" * 60)
    print(f"🎯 RESUMEN: {success_count}/{total_count} colecciones actualizadas/verificadas")
    print(f"📊 TOTAL: {success_count + 3}/11 colecciones (3 existentes + {success_count} actualizadas)")
    
    if success_count == total_count:
        print("✅ ¡Todas las colecciones están listas con documentos de ejemplo!")
        print("🚀 KIPI backend puede funcionar correctamente")
        print("🔑 Google Drive OAuth debería funcionar ahora")
    else:
        print("⚠️ Algunas colecciones no se pudieron actualizar")
        print("🔍 Revisa los errores anteriores")
    
    print("\n💡 Las colecciones existentes se actualizaron con documentos de ejemplo")
    print("💡 Google Drive OAuth ahora tiene la estructura necesaria")

if __name__ == "__main__":
    main()
