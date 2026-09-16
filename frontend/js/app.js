let currentAmbito = "Todos";
let editingNoteId = null;
console.log("WEB-HA app.js loaded - v1.4.0 UI Polished");

window.showToast = function(message, type = 'success') {
  const container = document.getElementById("toast-container");
  if (!container) return;
  const toast = document.createElement("div");
  const bg = type === 'success' ? 'bg-emerald-600 text-white' : 'bg-blue-600 text-white';
  toast.className = `${bg} px-4 py-3 rounded-xl shadow-xl text-sm font-medium pointer-events-auto transform transition-all duration-300 translate-y-2 opacity-0 flex items-center space-x-2`;
  toast.innerHTML = `<span>${type === 'success' ? '✅' : 'ℹ️'}</span><span>${message}</span>`;
  container.appendChild(toast);
  
  setTimeout(() => {
    toast.classList.remove("translate-y-2", "opacity-0");
  }, 10);

  setTimeout(() => {
    toast.classList.add("translate-y-2", "opacity-0");
    setTimeout(() => toast.remove(), 300);
  }, 3000);
};

window.renderApp = async function() {
  const notes = await window.localDB.getAllNotes();
  const container = document.getElementById("notes-container");
  if (!container) return;

  const activeNotes = notes.filter(n => !n.is_deleted);
  const filtered = currentAmbito === "Todos" 
    ? activeNotes 
    : activeNotes.filter(n => n.ambito === currentAmbito);

  // Sort: uncompleted first, completed (realizada) at the bottom
  filtered.sort((a, b) => (a.realizada || 0) - (b.realizada || 0));

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="col-span-full text-center py-16 px-4 bg-slate-900/40 rounded-2xl border border-slate-800/80">
        <div class="text-4xl mb-3">📭</div>
        <h3 class="text-base font-semibold text-slate-300 mb-1">No hay notas ni tareas en este ámbito</h3>
        <p class="text-xs text-slate-500">Crea una nueva nota o tarea haciendo clic en el botón superior.</p>
      </div>`;
    return;
  }

  container.innerHTML = filtered.map(note => {
    const isDone = note.realizada === 1;
    const cardBg = isDone ? "bg-slate-900/40 border-slate-800/60 opacity-60" : "bg-slate-900/80 border border-slate-800 shadow-xl hover:border-slate-700";
    const textStyle = isDone ? "line-through text-slate-400" : "text-slate-100";
    const descStyle = isDone ? "line-through text-slate-500" : "text-slate-300";

    return `
      <div class="${cardBg} rounded-2xl p-5 flex flex-col justify-between transition-all duration-200">
        <div>
          <div class="flex justify-between items-start mb-3">
            <span class="text-xs uppercase tracking-wider px-3 py-1 bg-blue-950/80 text-blue-300 rounded-full font-semibold border border-blue-800/40">${note.ambito}</span>
            <span class="text-xs text-slate-400 font-medium">${note.limite ? '📅 ' + note.limite : ''}</span>
          </div>
          <h3 class="text-base font-bold ${textStyle} mb-2">${escapeHtml(note.titulo)}</h3>
          <p class="text-sm ${descStyle} mb-4 whitespace-pre-line leading-relaxed">${escapeHtml(note.descripcion || '')}</p>
          
          ${note.dependencias ? `<p class="text-xs text-amber-300/80 mb-2"><strong>Dependencias:</strong> ${escapeHtml(note.dependencias)}</p>` : ''}
          ${note.ubicacion ? `<p class="text-xs text-purple-300/80 mb-2"><strong>Ubicación:</strong> ${escapeHtml(note.ubicacion)}</p>` : ''}
          ${note.monto !== null && note.monto !== undefined ? `<p class="text-xs text-emerald-300/80 mb-2"><strong>Monto:</strong> $${note.monto} ${note.estado ? '(' + note.estado + ')' : ''}</p>` : ''}
          ${note.transcripcion ? `<div class="bg-slate-950 p-3 rounded-xl text-xs text-slate-300 mb-3 border border-slate-800">🎙️ <strong>Transcripción:</strong> ${escapeHtml(note.transcripcion)}</div>` : ''}
          ${note.archivo_url ? `<audio controls src="${note.archivo_url}" class="w-full h-8 mb-3 rounded-lg"></audio>` : ''}
        </div>
        
        <div class="flex justify-between items-center pt-3 border-t border-slate-800/80 mt-2">
          <label class="flex items-center space-x-2 cursor-pointer text-xs text-slate-300 select-none">
            <input type="checkbox" ${isDone ? 'checked' : ''} onchange="toggleRealizada('${note.id}', this.checked)" class="rounded bg-slate-950 border-slate-700 text-blue-600 focus:ring-blue-500 w-4 h-4">
            <span>Realizada</span>
          </label>
          <div class="space-x-3">
            <button onclick="editNoteItem('${note.id}')" class="text-xs font-medium text-blue-400 hover:text-blue-300 transition">Editar</button>
            <button onclick="deleteNoteItem('${note.id}')" class="text-xs font-medium text-red-400 hover:text-red-300 transition">Eliminar</button>
          </div>
        </div>
      </div>
    `;
  }).join("");
};

function escapeHtml(str) {
  return (str || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

window.filterAmbito = function(ambito) {
  currentAmbito = ambito;
  document.querySelectorAll(".ambito-btn").forEach(btn => {
    if (btn.dataset.ambito === ambito) {
      btn.className = "ambito-btn px-4 py-2 rounded-xl font-medium text-sm bg-blue-600 text-white shadow-lg shadow-blue-600/20 transition";
    } else {
      btn.className = "ambito-btn px-4 py-2 rounded-xl font-medium text-sm bg-slate-900 text-slate-300 hover:bg-slate-800 transition border border-slate-800";
    }
  });
  window.renderApp();
};

window.toggleRealizada = async function(id, realizada) {
  const note = await window.localDB.getNote(id);
  if (note) {
    note.realizada = realizada ? 1 : 0;
    note.updated_at = new Date().toISOString();
    await window.localDB.saveNote(note);
    if (window.syncManager && window.syncManager.isOnline) {
      window.syncManager.syncWithServer();
    }
    window.showToast(realizada ? "Tarea marcada como realizada" : "Tarea marcada como pendiente", "info");
    window.renderApp();
  }
};

window.deleteNoteItem = async function(id) {
  if (confirm("¿Estás seguro de eliminar esta nota/tarea?")) {
    await window.localDB.deleteNoteLocally(id);
    if (window.syncManager && window.syncManager.isOnline) {
      window.syncManager.syncWithServer();
    }
    window.showToast("Nota eliminada correctamente", "info");
    window.renderApp();
  }
};

window.editNoteItem = async function(id) {
  const note = await window.localDB.getNote(id);
  if (note) {
    window.openModal(note);
  }
};

// Modal handlers
window.openModal = function(note = null) {
  document.getElementById("note-modal").classList.remove("hidden");
  const modalTitle = document.getElementById("modal-title");
  
  if (note) {
    editingNoteId = note.id;
    if (modalTitle) modalTitle.textContent = "Editar Nota o Tarea";
    document.getElementById("note-ambito").value = note.ambito || "Personal";
    document.getElementById("note-titulo").value = note.titulo || "";
    document.getElementById("note-descripcion").value = note.descripcion || "";
    document.getElementById("note-dependencias").value = note.dependencias || "";
    document.getElementById("note-ubicacion").value = note.ubicacion || "";
    document.getElementById("note-enterado").value = note.enterado || "";
    document.getElementById("note-limite").value = note.limite || "";
    document.getElementById("note-monto").value = note.monto !== null && note.monto !== undefined ? note.monto : "";
    document.getElementById("note-estado").value = note.estado || "";
  } else {
    editingNoteId = null;
    if (modalTitle) modalTitle.textContent = "Registrar Nueva Nota o Tarea";
    document.getElementById("note-form").reset();
    const today = new Date().toISOString().split("T")[0];
    document.getElementById("note-enterado").value = today;
  }
};

window.closeModal = function() {
  document.getElementById("note-modal").classList.add("hidden");
  document.getElementById("note-form").reset();
  document.getElementById("audio-preview-container").classList.add("hidden");
  editingNoteId = null;
};

let recordedAudioData = null;

window.toggleRecordAudio = async function() {
  const btn = document.getElementById("record-audio-btn");
  if (!window.audioRecorder.isRecording) {
    const started = await window.audioRecorder.startRecording();
    if (started) {
      btn.textContent = "⏹️ Detener Grabación";
      btn.className = "px-4 py-2 bg-red-600 text-white font-medium rounded-lg text-sm";
    }
  } else {
    btn.textContent = "🎙️ Procesando audio...";
    const result = await window.audioRecorder.stopRecording();
    btn.textContent = "🎙️ Grabar Audio";
    btn.className = "px-4 py-2 bg-purple-600 text-white font-medium rounded-lg text-sm";
    
    if (result) {
      recordedAudioData = result;
      const preview = document.getElementById("audio-preview-container");
      preview.classList.remove("hidden");
      document.getElementById("audio-player").src = result.file_url;
      document.getElementById("note-transcripcion").value = result.transcripcion || "";
      if (!document.getElementById("note-titulo").value) {
        document.getElementById("note-titulo").value = "Nota de voz: " + (result.transcripcion ? result.transcripcion.slice(0, 30) + "..." : "Audio");
      }
      window.showToast("Audio transcrito exitosamente", "success");
    }
  }
};

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("note-form");
  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      
      let existingNote = editingNoteId ? await window.localDB.getNote(editingNoteId) : null;
      
      const id = editingNoteId || ("note_" + Date.now() + "_" + Math.random().toString(36).substr(2, 9));
      const ambito = document.getElementById("note-ambito").value;
      const titulo = document.getElementById("note-titulo").value;
      const descripcion = document.getElementById("note-descripcion").value;
      const dependencias = document.getElementById("note-dependencias").value;
      const ubicacion = document.getElementById("note-ubicacion").value;
      const enterado = document.getElementById("note-enterado").value;
      const limite = document.getElementById("note-limite").value;
      const monto = parseFloat(document.getElementById("note-monto").value) || null;
      const estado = document.getElementById("note-estado").value || null;
      const transcripcion = recordedAudioData ? recordedAudioData.transcripcion : (existingNote ? existingNote.transcripcion : null);
      const archivo_url = recordedAudioData ? recordedAudioData.file_url : (existingNote ? existingNote.archivo_url : null);

      const updatedNote = {
        id,
        ambito,
        titulo,
        descripcion,
        dependencias,
        ubicacion,
        enterado,
        limite,
        realizada: existingNote ? existingNote.realizada : 0,
        monto,
        estado,
        tipo: archivo_url ? "audio" : (existingNote ? existingNote.tipo : "texto"),
        archivo_url,
        transcripcion,
        updated_at: new Date().toISOString(),
        is_deleted: 0
      };

      await window.localDB.saveNote(updatedNote);
      recordedAudioData = null;
      editingNoteId = null;
      window.closeModal();
      window.renderApp();

      window.showToast(existingNote ? "Nota actualizada con éxito" : "Nota creada con éxito", "success");

      if (window.syncManager && window.syncManager.isOnline) {
        window.syncManager.syncWithServer();
      }
    });
  }

  window.localDB.init().then(() => {
    window.renderApp();
  });
});
