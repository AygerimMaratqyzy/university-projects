import pygame
import os


class MusicPlayer:
    def __init__(self, music_folder):
        self.music_folder = music_folder
        self.playlist = self.load_music()
        self.index = 0

        self.is_playing = False
        self.paused = False

        pygame.mixer.init()

    # LOAD MUSIC FILES
    def load_music(self):
        files = []
        for file in os.listdir(self.music_folder):
            if file.endswith(".mp3") or file.endswith(".wav"):
                files.append(os.path.join(self.music_folder, file))
        files.sort()
        return files

    # PLAY / RESUME
    def play(self):
        if not self.playlist:
            return

        if self.paused:
            pygame.mixer.music.unpause()
            self.paused = False
            self.is_playing = True
            return

        pygame.mixer.music.load(self.playlist[self.index])
        pygame.mixer.music.play()
        self.is_playing = True

    # PAUSE
    def pause(self):
        pygame.mixer.music.pause()
        self.paused = True
        self.is_playing = False

    # STOP
    def stop(self):
        pygame.mixer.music.stop()
        self.paused = False
        self.is_playing = False

    # NEXT TRACK
    def next(self):
        if not self.playlist:
            return
        self.index = (self.index + 1) % len(self.playlist)
        self.paused = False
        self.play()

    # PREVIOUS TRACK
    def previous(self):
        if not self.playlist:
            return
        self.index = (self.index - 1) % len(self.playlist)
        self.paused = False
        self.play()

    # GET TRACK + ARTIST
    def get_track_info(self):
        if not self.playlist:
            return "Unknown", "No music"

        filename = os.path.basename(self.playlist[self.index])

        # Remove extension
        name = os.path.splitext(filename)[0]

        # Format: Artist - Track
        if " - " in name:
            artist, track = name.split(" - ", 1)
        else:
            artist = "Unknown"
            track = name

        return artist, track

    # PLAYLIST POSITION
    def get_position(self):
        if not self.playlist:
            return "0/0"
        return f"{self.index + 1}/{len(self.playlist)}"