import whisper
import os

# Путь к модели Whisper
model_path = os.path.join(os.path.dirname(__file__), 'whisper')

def transcribe_audio(audio_path):
    # Загрузка модели
    model = whisper.load_model("base", download_root=model_path)

    # Преобразование аудио в текст
    result = model.transcribe(audio_path)
    return result["text"]
