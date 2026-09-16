import os
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/calendar']

def authorize():
    cred_file = "credentials.json"
    token_path = "token.json"
    
    if not os.path.exists(cred_file):
        print(f"Error: No se encontró '{cred_file}' en la carpeta backend/")
        return

    print("Iniciando flujo de autorización de Google Calendar...")
    flow = InstalledAppFlow.from_client_secrets_file(cred_file, SCOPES)
    creds = flow.run_local_server(port=0)
    
    with open(token_path, "w") as token:
        token.write(creds.to_json())
    
    print(f"¡Autorización exitosa! Token guardado en '{token_path}'.")

if __name__ == "__main__":
    authorize()
