class AudioRecorder {
  constructor() {
    this.mediaRecorder = null;
    this.audioChunks = [];
    this.isRecording = false;
  }

  async startRecording() {
    this.audioChunks = [];
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      this.mediaRecorder = new MediaRecorder(stream);
      this.mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          this.audioChunks.push(e.data);
        }
      };
      this.mediaRecorder.start();
      this.isRecording = true;
      return true;
    } catch (e) {
      alert("No se pudo acceder al micrófono: " + e.message);
      return false;
    }
  }

  async stopRecording() {
    return new Promise((resolve) => {
      if (!this.mediaRecorder || !this.isRecording) {
        resolve(null);
        return;
      }
      this.mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(this.audioChunks, { type: "audio/webm" });
        this.isRecording = false;
        
        // Upload and transcribe
        const formData = new FormData();
        formData.append("file", audioBlob, "nota_voz.webm");

        try {
          const res = await fetch("/api/notes/upload-audio", {
            method: "POST",
            body: formData
          });
          const data = await res.json();
          resolve(data);
        } catch (e) {
          console.error("Error uploading audio:", e);
          resolve(null);
        }
      };
      this.mediaRecorder.stop();
      // Stop tracks
      this.mediaRecorder.stream.getTracks().forEach(track => track.stop());
    });
  }
}

window.audioRecorder = new AudioRecorder();
