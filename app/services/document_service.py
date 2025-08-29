from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from app.config.database import DatabaseConfig
from app.models.document import DocumentCreate, DocumentUpdate, DocumentResponse

class DocumentService:
    """Servicio para gestión de documentos"""
    
    def __init__(self):
        self.db = DatabaseConfig.get_firestore_client()
    
    async def get_user_documents(self, user_id: str) -> List[DocumentResponse]:
        """Obtener todos los documentos de un usuario"""
        try:
            docs = self.db.collection('documents').where('user_id', '==', user_id).stream()
            documents = []
            for doc in docs:
                doc_data = doc.to_dict()
                doc_data['id'] = doc.id
                documents.append(DocumentResponse(**doc_data))
            return documents
        except Exception as e:
            print(f"Error obteniendo documentos: {e}")
            return []
    
    async def get_document_by_id(self, document_id: str, user_id: str) -> Optional[DocumentResponse]:
        """Obtener documento por ID"""
        try:
            doc_ref = self.db.collection('documents').document(document_id)
            doc = doc_ref.get()
            
            if doc.exists:
                doc_data = doc.to_dict()
                if doc_data.get('user_id') == user_id:
                    doc_data['id'] = document_id
                    return DocumentResponse(**doc_data)
            return None
        except Exception as e:
            print(f"Error obteniendo documento: {e}")
            return None
    
    async def create_document(self, user_id: str, document_data: DocumentCreate) -> DocumentResponse:
        """Crear nuevo documento"""
        try:
            doc_dict = document_data.dict()
            doc_dict['user_id'] = user_id
            doc_dict['created_at'] = datetime.now()
            doc_dict['updated_at'] = datetime.now()
            doc_dict['is_archived'] = False
            doc_dict['is_favorite'] = False
            
            doc_ref = self.db.collection('documents').add(doc_dict)
            doc_dict['id'] = doc_ref[1].id
            
            return DocumentResponse(**doc_dict)
        except Exception as e:
            print(f"Error creando documento: {e}")
            raise
    
    async def update_document(self, document_id: str, user_id: str, document_data: DocumentUpdate) -> Optional[DocumentResponse]:
        """Actualizar documento"""
        try:
            doc_ref = self.db.collection('documents').document(document_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return None
            
            doc_data = doc.to_dict()
            if doc_data.get('user_id') != user_id:
                return None
            
            update_data = document_data.dict(exclude_unset=True)
            update_data['updated_at'] = datetime.now()
            
            doc_ref.update(update_data)
            
            # Obtener documento actualizado
            updated_doc = doc_ref.get().to_dict()
            updated_doc['id'] = document_id
            
            return DocumentResponse(**updated_doc)
        except Exception as e:
            print(f"Error actualizando documento: {e}")
            return None
    
    async def delete_document(self, document_id: str, user_id: str) -> bool:
        """Eliminar documento"""
        try:
            doc_ref = self.db.collection('documents').document(document_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return False
            
            doc_data = doc.to_dict()
            if doc_data.get('user_id') != user_id:
                return False
            
            doc_ref.delete()
            return True
        except Exception as e:
            print(f"Error eliminando documento: {e}")
            return False
    
    async def get_document_categories(self, user_id: str) -> List[str]:
        """Obtener categorías de documentos del usuario"""
        try:
            docs = self.db.collection('documents').where('user_id', '==', user_id).stream()
            categories = set()
            for doc in docs:
                doc_data = doc.to_dict()
                if doc_data.get('category'):
                    categories.add(doc_data['category'])
            return list(categories)
        except Exception as e:
            print(f"Error obteniendo categorías: {e}")
            return []
    
    async def get_expiring_documents(self, user_id: str, days: int = 30) -> List[DocumentResponse]:
        """Obtener documentos que vencen pronto"""
        try:
            docs = self.db.collection('documents').where('user_id', '==', user_id).stream()
            expiring_docs = []
            cutoff_date = datetime.now() + timedelta(days=days)
            
            for doc in docs:
                doc_data = doc.to_dict()
                if doc_data.get('expiry_date'):
                    try:
                        expiry_date = datetime.fromisoformat(doc_data['expiry_date'].replace('Z', '+00:00'))
                        if expiry_date <= cutoff_date:
                            doc_data['id'] = doc.id
                            expiring_docs.append(DocumentResponse(**doc_data))
                    except ValueError:
                        continue
            
            return expiring_docs
        except Exception as e:
            print(f"Error obteniendo documentos por vencer: {e}")
            return []
    
    async def search_documents(self, user_id: str, query: str) -> List[DocumentResponse]:
        """Buscar documentos por texto"""
        try:
            docs = self.db.collection('documents').where('user_id', '==', user_id).stream()
            matching_docs = []
            query_lower = query.lower()
            
            for doc in docs:
                doc_data = doc.to_dict()
                # Buscar en nombre, descripción y categoría
                if (query_lower in doc_data.get('name', '').lower() or
                    query_lower in doc_data.get('description', '').lower() or
                    query_lower in doc_data.get('category', '').lower()):
                    doc_data['id'] = doc.id
                    matching_docs.append(DocumentResponse(**doc_data))
            
            return matching_docs
        except Exception as e:
            print(f"Error buscando documentos: {e}")
            return []
