import os
import requests
import higgsfield_client  # Import correcto
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Google Auth (Sheets + Drive)
creds_dict = eval(os.environ['GOOGLE_SERVICE_ACCOUNT_JSON'])
creds = Credentials.from_service_account_info(
    creds_dict,
    scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
)
sheets_client = gspread.authorize(creds)
drive_service = build('drive', 'v3', credentials=creds)

# Sheet y prompts
sheet = sheets_client.open("PromptsDiariosAI").sheet1  # Cambia nombre si necesario
prompts = sheet.col_values(1)[1:31]  # Toma hasta 30 prompts

# Folder Drive ID
DRIVE_FOLDER_ID = "1yHBgw4JDy3F_nBsfs7nRF3VUCE4D4v_y"

# Auth Higgsfield (usa HF_KEY)
os.environ['HF_KEY'] = os.environ['HF_KEY']  # Ya está en env

for i, prompt in enumerate(prompts):
    if not prompt.strip():
        continue
    print(f"Generando video {i+1}: {prompt}")

    # MODEL: Reemplaza con tu exacto, ej: 'higgsfield/dop-standard-first-last-frame'
    MODEL = "REEMPLAZA_CON_MODEL_FIRST_LAST_FRAME"  # <<< AQUÍ EL EXACTO >>>

    result = higgsfield_client.subscribe(
        MODEL,
        arguments={
            'prompt': prompt.strip() + ", cinematic motion, smooth animation",  # Motion prompt
            # Para first/last frame models, agrega si el modelo lo requiere:
            'first_frame_prompt': prompt.strip() + ", initial frame, detailed",
            'last_frame_prompt': prompt.strip() + ", final frame, dynamic",
            'duration': 20,
            'aspect_ratio': '9:16',
            'resolution': '1080p',
            # Prueba otros params: 'motion_strength': 'high', etc.
        }
    )

    # Debug: Imprime result para ver estructura
    print("Result structure:", result)

    # Extrae video URL (adapta según print)
    try:
        video_url = result['video']['url']  # Común
    except:
        try:
            video_url = result['videos'][0]['url']
        except:
            video_url = result['output'][0]  # Otra común
            print("URL no estándar, checa print")

    # Descarga
    video_data = requests.get(video_url).content
    video_path = f"video_{i+1}.mp4"
    with open(video_path, "wb") as f:
        f.write(video_data)

    # Sube Drive
    file_metadata = {'name': f"video_{i+1}.mp4", 'parents': [DRIVE_FOLDER_ID]}
    media = MediaFileUpload(video_path, mimetype='video/mp4')
    drive_service.files().create(body=file_metadata, media_body=media).execute()

    os.remove(video_path)

print("¡30 videos listos en Drive!")
