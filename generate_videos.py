import os
from higgsfield import HiggsfieldClient
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Higgsfield Client
client = HiggsfieldClient(api_key=os.environ['HIGGSFIELD_API_KEY'])

# Google Auth (Sheets + Drive)
creds = Credentials.from_service_account_info(
    info=dict(eval(os.environ['GOOGLE_SERVICE_ACCOUNT_JSON'])),  # Convierte string JSON a dict
    scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
)
sheets_client = gspread.authorize(creds)
drive_service = build('drive', 'v3', credentials=creds)

# Abre Sheet y lee prompts
sheet = sheets_client.open("PromptsDiariosAI").sheet1  
prompts = sheet.col_values(1)[1:]  # Columna A, salta header 

# Folder en Drive para videos 
DRIVE_FOLDER_ID = "1yHBgw4JDy3F_nBsfs7nRF3VUCE4D4v_y"  # Ej: de https://drive.google.com/drive/folders/abc123 → abc123

for i, prompt in enumerate(prompts[:30]):  # Máximo 30
    print(f"Generando video {i+1}: {prompt}")
    
    # Genera video (adapta params según docs Higgsfield SDK)
    video_response = client.generate_video(
        prompt=prompt.strip(),
        duration=20,  # segundos
        aspect_ratio="9:16",  # vertical
        # Agrega más params como model="kling-pro" si tu plan lo tiene
    )
    
    # Asume SDK guarda o retorna path/bytes (adapta si retorna URL)
    video_path = f"video_{i+1}.mp4"
    video_response.save(video_path)  # O video_response.download(video_path) según docs
    
    # Sube a Drive
    file_metadata = {'name': f"video_{i+1}_{os.urandom(4).hex()}.mp4", 'parents': [DRIVE_FOLDER_ID]}
    media = MediaFileUpload(video_path, mimetype='video/mp4')
    drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    
    # Limpia local
    os.remove(video_path)

print("¡30 videos generados y subidos a Drive!")
