from services.stt import speech_to_text
from services.tts import text_to_speech
from graph import graph 

def process_audio(audio_file_path: str):
    user_text = speech_to_text(audio_file_path)

    result = graph.invoke({
        "user_text" : user_text
    })

    response_text = result["response_text"]
    response_mode = result["response_mode"]

    if response_mode == "speech" :
        audio_bytes = text_to_speech(response_text)

        return {
            "user_text": user_text,
            "response_text": response_text,
            "audio": audio_bytes,
        }

    return {
        "user_text": user_text,
        "response_text": response_text,
        "audio": None,
    }
