import os

model_size = "base"
model = None

def get_whisper_model():
    global model
    if model is None:
        try:
            from faster_whisper import WhisperModel
            model = WhisperModel(model_size, device="cpu", compute_type="int8")
        except Exception as e:
            print(f"Faster-whisper not available or failed to load: {e}")
            model = False
    return model if model is not False else None

def transcribe_audio_file(file_path: str) -> str:
    try:
        w_model = get_whisper_model()
        if not w_model:
            return "Transcripción no disponible (dependencia av/faster-whisper no instalada en entorno local)."
        segments, info = w_model.transcribe(file_path, beam_size=5)
        text = " ".join([segment.text for segment in segments])
        return text.strip()
    except Exception as e:
        print(f"Transcription error: {e}")
        return f"Error transcribiendo audio: {str(e)}"
