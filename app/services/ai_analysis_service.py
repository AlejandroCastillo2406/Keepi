from typing import Dict, Any, List, Optional
import tempfile
import os
from PIL import Image
import pytesseract
from datetime import datetime, timedelta
import re

class DocumentAnalysisService:
    """Servicio para análisis automático de documentos usando AI"""
    
    def __init__(self):
        # Configurar ruta de Tesseract si es necesario
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        pass
    
    async def analyze_document(self, content: bytes, content_type: str, filename: str) -> Dict[str, Any]:
        """Analizar documento y extraer información automáticamente"""
        try:
            # Extraer texto del documento
            extracted_text = await self._extract_text(content, content_type, filename)
            
            # Clasificar documento
            suggested_category = await self._classify_document(extracted_text, filename)
            
            # Extraer metadatos
            metadata = await self._extract_metadata(extracted_text)
            
            # Generar tags
            tags = await self._generate_tags(extracted_text, suggested_category)
            
            # Calcular confianza
            confidence_score = await self._calculate_confidence(extracted_text, suggested_category)
            
            # Extraer fecha de vencimiento
            expiry_date = await self._extract_expiry_date(extracted_text)
            
            # Extraer número de documento
            document_number = await self._extract_document_number(extracted_text)
            
            # Extraer organización
            organization = await self._extract_organization(extracted_text)
            
            return {
                "suggested_category": suggested_category,
                "confidence_score": confidence_score,
                "extracted_text": extracted_text,
                "metadata": metadata,
                "tags": tags,
                "expiry_date": expiry_date,
                "document_number": document_number,
                "organization": organization,
                "processing_time_ms": 0,  # TODO: Implementar medición de tiempo
                "ai_model_version": "1.0.0"
            }
            
        except Exception as e:
            print(f"Error analizando documento: {e}")
            # Retornar análisis básico en caso de error
            return {
                "suggested_category": "General",
                "confidence_score": 0.1,
                "extracted_text": "",
                "metadata": {},
                "tags": ["error"],
                "expiry_date": None,
                "document_number": None,
                "organization": None,
                "processing_time_ms": 0,
                "ai_model_version": "1.0.0"
            }
    
    async def _extract_text(self, content: bytes, content_type: str, filename: str) -> str:
        """Extraer texto del documento según su tipo"""
        try:
            if content_type.startswith('image/'):
                # Procesar imagen con OCR
                return await self._extract_text_from_image(content)
            elif content_type == 'application/pdf':
                # Por ahora, retornar nombre del archivo (sin PyMuPDF)
                return f"PDF: {filename}"
            else:
                # Para otros tipos, intentar decodificar como texto
                try:
                    return content.decode('utf-8')
                except:
                    return f"Archivo: {filename}"
                    
        except Exception as e:
            print(f"Error extrayendo texto: {e}")
            return f"Error extrayendo texto: {filename}"
    
    async def _extract_text_from_image(self, content: bytes) -> str:
        """Extraer texto de imagen usando OCR"""
        try:
            # Crear archivo temporal
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            try:
                # Abrir imagen con Pillow
                image = Image.open(temp_file_path)
                
                # Extraer texto con Tesseract
                text = pytesseract.image_to_string(image, lang='spa+eng')
                
                # Limpiar archivo temporal
                os.unlink(temp_file_path)
                
                return text.strip()
                
            except Exception as e:
                # Limpiar archivo temporal en caso de error
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                raise e
                
        except Exception as e:
            print(f"Error en OCR: {e}")
            return "Error en OCR"
    
    async def _classify_document(self, text: str, filename: str) -> str:
        """Clasificar documento basado en contenido y nombre"""
        text_lower = text.lower()
        filename_lower = filename.lower()
        
        # Palabras clave para clasificación
        keywords = {
            "Factura": ["factura", "invoice", "bill", "recibo", "pago"],
            "Contrato": ["contrato", "contract", "acuerdo", "convenio"],
            "Identificación": ["dni", "pasaporte", "carnet", "identidad", "id"],
            "Recibo": ["recibo", "comprobante", "voucher", "ticket"],
            "Documento Legal": ["legal", "judicial", "notarial", "oficial"],
            "Certificado": ["certificado", "certificate", "diploma", "título"],
            "Reporte": ["reporte", "report", "informe", "estudio"],
            "Manual": ["manual", "guía", "instrucciones", "tutorial"]
        }
        
        # Buscar coincidencias
        for category, words in keywords.items():
            for word in words:
                if word in text_lower or word in filename_lower:
                    return category
        
        # Si no hay coincidencias, clasificar por extensión
        if filename.endswith('.pdf'):
            return "Documento PDF"
        elif filename.endswith(('.jpg', '.jpeg', '.png')):
            return "Imagen"
        else:
            return "General"
    
    async def _extract_metadata(self, text: str) -> Dict[str, Any]:
        """Extraer metadatos del texto"""
        metadata = {}
        
        # Buscar fechas
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{4}',  # DD/MM/YYYY
            r'\d{1,2}-\d{1,2}-\d{4}',  # DD-MM-YYYY
            r'\d{4}-\d{1,2}-\d{1,2}',  # YYYY-MM-DD
        ]
        
        dates_found = []
        for pattern in date_patterns:
            dates = re.findall(pattern, text)
            dates_found.extend(dates)
        
        if dates_found:
            metadata['fechas_encontradas'] = list(set(dates_found))
        
        # Buscar montos
        amount_patterns = [
            r'S/\.\s*\d+[,.]?\d*',  # S/. 150.00
            r'\$\s*\d+[,.]?\d*',    # $ 150.00
            r'\d+[,.]?\d*\s*USD',   # 150.00 USD
        ]
        
        amounts_found = []
        for pattern in amount_patterns:
            amounts = re.findall(pattern, text)
            amounts_found.extend(amounts)
        
        if amounts_found:
            metadata['montos'] = list(set(amounts_found))
        
        # Buscar números de documento
        doc_patterns = [
            r'[A-Z]{1,3}-\d{4,}',  # F001-2024
            r'[A-Z]{1,3}\d{4,}',   # F0012024
            r'\d{4,}',              # 2024001
        ]
        
        doc_numbers = []
        for pattern in doc_patterns:
            numbers = re.findall(pattern, text)
            doc_numbers.extend(numbers)
        
        if doc_numbers:
            metadata['numeros_documento'] = list(set(doc_numbers))
        
        return metadata
    
    async def _generate_tags(self, text: str, category: str) -> List[str]:
        """Generar tags automáticamente"""
        tags = [category.lower()]
        
        # Agregar tags basados en el texto
        text_lower = text.lower()
        
        # Tags comunes
        common_tags = {
            "urgente": ["urgente", "inmediato", "asap"],
            "importante": ["importante", "crítico", "prioritario"],
            "confidencial": ["confidencial", "privado", "secreto"],
            "borrador": ["borrador", "draft", "temporal"]
        }
        
        for tag, keywords in common_tags.items():
            if any(keyword in text_lower for keyword in keywords):
                tags.append(tag)
        
        # Agregar tags por categoría
        category_tags = {
            "Factura": ["pago", "comercial", "servicio"],
            "Contrato": ["legal", "acuerdo", "obligatorio"],
            "Identificación": ["personal", "oficial", "identidad"],
            "Recibo": ["comprobante", "pago", "transacción"]
        }
        
        if category in category_tags:
            tags.extend(category_tags[category])
        
        return list(set(tags))[:10]  # Máximo 10 tags
    
    async def _calculate_confidence(self, text: str, category: str) -> float:
        """Calcular nivel de confianza de la clasificación"""
        if not text or text.strip() == "":
            return 0.1
        
        # Factores de confianza
        text_length = len(text)
        category_keywords = self._get_category_keywords(category)
        
        # Contar palabras clave encontradas
        matches = 0
        text_lower = text.lower()
        for keyword in category_keywords:
            if keyword in text_lower:
                matches += 1
        
        # Calcular confianza
        keyword_confidence = matches / len(category_keywords) if category_keywords else 0
        length_confidence = min(text_length / 1000, 1.0)  # Normalizar por longitud
        
        # Promedio ponderado
        confidence = (keyword_confidence * 0.7) + (length_confidence * 0.3)
        
        return round(confidence, 2)
    
    def _get_category_keywords(self, category: str) -> List[str]:
        """Obtener palabras clave para una categoría"""
        keywords = {
            "Factura": ["factura", "invoice", "bill", "recibo", "pago", "total", "subtotal"],
            "Contrato": ["contrato", "contract", "acuerdo", "convenio", "partes", "cláusula"],
            "Identificación": ["dni", "pasaporte", "carnet", "identidad", "nacionalidad"],
            "Recibo": ["recibo", "comprobante", "voucher", "ticket", "pago", "fecha"],
            "Documento Legal": ["legal", "judicial", "notarial", "oficial", "gobierno"],
            "Certificado": ["certificado", "certificate", "diploma", "título", "acreditación"],
            "Reporte": ["reporte", "report", "informe", "estudio", "análisis"],
            "Manual": ["manual", "guía", "instrucciones", "tutorial", "procedimiento"]
        }
        
        return keywords.get(category, [])
    
    async def _extract_expiry_date(self, text: str) -> Optional[str]:
        """Extraer fecha de vencimiento del texto"""
        # Buscar patrones de fecha de vencimiento
        expiry_patterns = [
            r'venc[ei]miento[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'expir[ae][:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'validez[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'vigencia[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})'
        ]
        
        for pattern in expiry_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    async def _extract_document_number(self, text: str) -> Optional[str]:
        """Extraer número de documento del texto"""
        # Buscar patrones de número de documento
        doc_patterns = [
            r'[Nn]úmero[:\s]*([A-Z]{1,3}[-]?\d{4,})',
            r'[Cc]ódigo[:\s]*([A-Z]{1,3}[-]?\d{4,})',
            r'[Rr]eferencia[:\s]*([A-Z]{1,3}[-]?\d{4,})',
            r'[Ii]D[:\s]*([A-Z]{1,3}[-]?\d{4,})'
        ]
        
        for pattern in doc_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    async def _extract_organization(self, text: str) -> Optional[str]:
        """Extraer nombre de organización del texto"""
        # Buscar patrones de organización
        org_patterns = [
            r'[Ee]mpresa[:\s]*([A-Z][a-z\s]+)',
            r'[Cc]ompañía[:\s]*([A-Z][a-z\s]+)',
            r'[Ii]nstitución[:\s]*([A-Z][a-z\s]+)',
            r'[Oo]rganización[:\s]*([A-Z][a-z\s]+)'
        ]
        
        for pattern in org_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
