import firebase_admin
from firebase_admin import credentials, firestore
import os

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

db = initialize_firebase()

print('Verificando colecciones:')
print('=' * 40)

# Lista de colecciones a verificar
collections = ['folders', 'ai_analysis', 'ai_analysis_history', 'audit_logs', 'search_index', 'backup_sync', 'sync_conflicts']

for col_name in collections:
    try:
        docs = list(db.collection(col_name).limit(1).stream())
        if docs:
            print(f'  {col_name}: Existe ({len(docs)} docs)')
        else:
            print(f'  {col_name}: Existe pero vacia (0 docs)')
    except Exception as e:
        print(f'  {col_name}: NO existe')

print('=' * 40)
print('Verificacion completada!')
