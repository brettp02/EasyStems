import customtkinter as ctk
import yt_dlp
import os
import threading
from tkinter import messagebox, filedialog
import sys

# Load custom theme
ctk_theme_path = os.path.join(os.path.dirname(__file__), 'custom_theme.json')
ctk.set_default_color_theme(ctk_theme_path)

# Set the appearance mode to match the system
ctk.set_appearance_mode("System")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        # Setup the GUI

        self.title("YouTube Audio Downloader with Stem Separation")
        self.geometry("500x350")
        self.resizable(False, False)

        self.default_font = ctk.CTkFont(family="SF Pro Text", size=13)
        self.title_font = ctk.CTkFont(family="SF Pro Text", size=20, weight="bold")

        self.main_frame = ctk.CTkFrame(self, corner_radius=6)
        self.main_frame.pack(padx=20, pady=20, fill="both", expand=True)

        self.title_label = ctk.CTkLabel(self.main_frame, text="EasyStems", font=self.title_font)
        self.title_label.pack(pady=(10, 20))

        self.url_entry = ctk.CTkEntry(self.main_frame, placeholder_text="Enter YouTube URL here...", width=400, height=30, font=self.default_font)
        self.url_entry.pack(pady=10)

        self.download_button = ctk.CTkButton(self.main_frame, text="Download and Separate Stems", command=self.download_audio, width=140, height=30, font=self.default_font)
        self.download_button.pack(pady=20)

        self.progress_bar = ctk.CTkProgressBar(self.main_frame, width=400, height=10)
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(self.main_frame, text="", font=self.default_font)
        self.status_label.pack(pady=(5, 0))

        self.url_entry.focus()

    def download_audio(self):
        # Handle URL entry and download Button
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning(title="Input Error", message="Please enter a YouTube URL.")
            return
        
        self.download_button.configure(state="disabled")
        self.status_label.configure(text="Starting download...")
        threading.Thread(target=self.download_thread, args=(url,), daemon=True).start()

    def download_thread(self, url):
        # Logic for downloading using yt_dlp
        def progress_hook(d):
            if d["status"] == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate")
                downloaded = d.get("downloaded_bytes", 0)
                if total:
                    percent = downloaded / total
                    self.progress_bar.set(percent)
                    self.status_label.configure(text=f"Downloading... {int(percent * 100)}%")
            elif d["status"] == "finished":
                self.progress_bar.set(1.0)
                self.status_label.configure(text="Download completed.")

        home_dir = os.path.expanduser("~")
        output_template = os.path.join(home_dir, 'downloaded_audio.%(ext)s')

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": output_template,
            "progress_hooks": [progress_hook],
            "quiet": True,
            "no_warnings": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "wav",
                    "preferredquality": "192",
                }
            ],
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            save_path = filedialog.asksaveasfilename(defaultextension=".wav", filetypes=[("Audio Files", "*.wav")], title="Save Audio File")
            temp_file = os.path.join(home_dir, 'downloaded_audio.wav')
            if save_path:
                os.replace(temp_file, save_path)
                self.status_label.configure(text="Audio downloaded. Starting stem separation...")
                self.separate_stems(save_path)
            else:
                os.remove(temp_file)
            self.status_label.configure(text="Ready")
        except Exception as e:
            messagebox.showerror(title="Download Error", message=str(e))
            self.status_label.configure(text="An error occurred.")
        finally:
            self.progress_bar.set(0)
            self.download_button.configure(state="normal")

    def separate_stems(self, audio_path):
        # Use Demucs model to split the recently downloaded wav file into 4 stems
        try:
            desktop_folder = os.path.join(os.path.expanduser("~"), "Desktop", "Stems")
            if not os.path.exists(desktop_folder):
                os.makedirs(desktop_folder)

            command = f"demucs --out {desktop_folder} \"{audio_path}\""
            os.system(command)  # Use os.system to run the Demucs command

            # Notify user of completion and the location of the stems
            messagebox.showinfo(title="Success", message=f"Stem separation completed! Stems saved in {desktop_folder}")
        except Exception as e:
            messagebox.showerror(title="Separation Error", message=str(e))

if __name__ == "__main__":
    app = App()
    app.mainloop()
