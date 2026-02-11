import os
import requests
import higgsfield_client
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
sheet = sheets_client.open("PromptsDiariosAI").sheet1
prompts = sheet.col_values(1)[1:31]  # Columna A, hasta 30 prompts

# Folder Drive ID
DRIVE_FOLDER_ID = "1yHBgw4JDy3F_nBsfs7nRF3VUCE4D4v_y"

# Modelos Higgsfield
TEXT_TO_IMAGE_MODEL = "higgsfield-ai/soul/standard"
IMAGE_TO_VIDEO_MODEL = "higgsfield-ai/dop/lite/first-last-frame"


def generate_image(prompt_text):
    """Genera una imagen con Soul Standard y retorna la URL."""
    result = higgsfield_client.subscribe(
        TEXT_TO_IMAGE_MODEL,
        arguments={
            'prompt': prompt_text,
        }
    )
    print("Image result:", result)
    # Extrae URL de imagen (adapta según estructura real del response)
    try:
        return result['image']['url']
    except (KeyError, TypeError):
        try:
            return result['images'][0]['url']
        except (KeyError, TypeError, IndexError):
            return result['output'][0]


for i, prompt in enumerate(prompts):
    if not prompt.strip():
        continue
    print(f"\n=== Video {i+1}: {prompt} ===")

    # Paso 1: Generar first frame image
    first_prompt = prompt.strip() + ", establishing shot, initial scene, detailed composition"
    print(f"Generando first frame: {first_prompt}")
    first_frame_url = generate_image(first_prompt)
    print(f"First frame URL: {first_frame_url}")

    # Paso 2: Generar last frame image (variación del prompt)
    last_prompt = prompt.strip() + ", final scene, dynamic conclusion, dramatic angle"
    print(f"Generando last frame: {last_prompt}")
    last_frame_url = generate_image(last_prompt)
    print(f"Last frame URL: {last_frame_url}")

    # Paso 3: Generar video con DoP Lite first-last-frame
    print("Generando video con DoP Lite...")
    video_result = higgsfield_client.subscribe(
        IMAGE_TO_VIDEO_MODEL,
        arguments={
            'prompt': prompt.strip() + ", cinematic motion, smooth animation",
            'first_frame_image': first_frame_url,
            'last_frame_image': last_frame_url,
            'enhance_prompt': True,
        }
    )
    print("Video result:", video_result)

    # Extrae video URL
    try:
        video_url = video_result['video']['url']
    except (KeyError, TypeError):
        try:
            video_url = video_result['videos'][0]['url']
        except (KeyError, TypeError, IndexError):
            video_url = video_result['output'][0]
            print("URL format no estándar, checa print arriba")

    # Descarga video
    video_data = requests.get(video_url).content
    video_path = f"video_{i+1}.mp4"
    with open(video_path, "wb") as f:
        f.write(video_data)

    # Sube a Drive
    file_metadata = {'name': f"video_{i+1}.mp4", 'parents': [DRIVE_FOLDER_ID]}
    media = MediaFileUpload(video_path, mimetype='video/mp4')
    drive_service.files().create(body=file_metadata, media_body=media).execute()
    print(f"Video {i+1} subido a Drive!")

    os.remove(video_path)

print("\n¡Videos listos en Drive!")
