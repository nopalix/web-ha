class SyncManager {
  constructor() {
    this.isOnline = navigator.onLine;
    window.addEventListener("online", () => this.handleOnline());
    window.addEventListener("offline", () => this.handleOffline());
  }

  init() {
    this.updateStatusIndicator();
    if (this.isOnline) {
      this.syncWithServer();
    }
  }

  handleOnline() {
    this.isOnline = true;
    this.updateStatusIndicator();
    this.syncWithServer();
  }

  handleOffline() {
    this.isOnline = false;
    this.updateStatusIndicator();
  }

  updateStatusIndicator() {
    const indicator = document.getElementById("sync-status");
    if (indicator) {
      indicator.textContent = this.isOnline ? "🟢 Online" : "🔴 Offline (Local Mode)";
      indicator.className = this.isOnline ? "text-green-400 font-medium text-sm" : "text-red-400 font-medium text-sm";
    }
  }

  async syncWithServer() {
    if (!this.isOnline) return;
    try {
      const localNotes = await window.localDB.getAllNotes();
      const response = await fetch("/api/sync/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ notes: localNotes })
      });
      if (!response.ok) return;
      const data = await response.json();
      
      // Update local DB with server notes (Last-write-wins handled or server state merged)
      if (data.server_notes) {
        for (const sNote of data.server_notes) {
          await window.localDB.saveNote(sNote);
        }
      }
      if (window.renderApp) {
        window.renderApp();
      }
    } catch (e) {
      console.error("Sync error:", e);
    }
  }
}

window.syncManager = new SyncManager();
window.addEventListener("DOMContentLoaded", () => {
  window.syncManager.init();
});
