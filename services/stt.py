import os
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

load_dotenv()

client = ElevenLabs(
    api_key=os.getenv("ELEVENLABS_API_KEY")
)

def speech_to_text(audio_file_path: str) -> str :
    with open(audio_file_path , "rb") as audio_file:
        transcription = client.speech_to_text.convert(
            audio=audio_file , 
            model_id="scribe_v2",
            tag_audio_events=False,
            diarize=False,
        )

    return transcription.text