import firebase_admin
from firebase_admin import credentials, auth

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

def verify_admin_token(id_token: str):
    decoded = auth.verify_id_token(id_token)
    return decoded
