"""
Music Player Module for Maahi Robot Assistant
Plays music from YouTube using ytmusicapi + mpv
Audio output: alsa/plughw:CARD=Headphones,DEV=0
"""
import logging
import os
import subprocess
from config import SEARCH_RESULTS_LIMIT, TEMP_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from ytmusicapi import YTMusic
except ImportError:
    logger.warning("ytmusicapi not installed. Run: pip install ytmusicapi")


class MusicPlayer:

    def __init__(self):
        self.is_playing    = False
        self.current_song  = None
        self.current_artist = None
        self.play_process  = None

        try:
            self.ytmusic = YTMusic()
            logger.info("YouTube Music API initialized")
        except Exception as e:
            logger.warning(f"YTMusic init failed: {e}")
            self.ytmusic = None

    def search_songs(self, query, limit=SEARCH_RESULTS_LIMIT):
        try:
            if not self.ytmusic:
                logger.error("YTMusic not initialized")
                return []

            logger.info(f"Searching: {query}")
            results = self.ytmusic.search(query, filter="songs", limit=limit)

            songs = []
            for result in results:
                song_info = {
                    "title":    result.get("title", "Unknown"),
                    "artist":   result.get("artists", [{}])[0].get("name", "Unknown")
                                if result.get("artists") else "Unknown",
                    "video_id": result.get("videoId", ""),
                    "duration": result.get("duration", "")
                }
                if song_info["video_id"]:
                    songs.append(song_info)
                    logger.info(f"  - {song_info['title']} by {song_info['artist']}")

            return songs

        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    def search_by_mood(self, mood, limit=SEARCH_RESULTS_LIMIT):
        mood_queries = {
            "happy":        "happy upbeat songs",
            "sad":          "sad emotional songs",
            "energetic":    "energetic workout music",
            "relaxing":     "relaxing calm music",
            "workout":      "workout pump up music",
            "party":        "party dance songs",
            "love":         "romantic love songs",
            "bollywood":    "bollywood hits",
            "instrumental": "instrumental music"
        }
        search_term = mood_queries.get(mood.lower(), f"{mood} music")
        return self.search_songs(search_term, limit)

    def play_song_by_video_id(self, video_id, title="", artist=""):
        try:
            if not video_id:
                logger.error("No video ID provided")
                return False

            self.stop_playback()

            self.current_song   = title
            self.current_artist = artist
            logger.info(f"Playing: {title} by {artist}")

            url = f"https://www.youtube.com/watch?v={video_id}"

            self.play_process = subprocess.Popen(
                [
                    "mpv",
                    "--no-video",
                    "--audio-device=alsa/plughw:CARD=Headphones,DEV=0",
                    "--really-quiet",
                    url
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            self.is_playing = True
            logger.info("Playback started")
            return True

        except FileNotFoundError:
            logger.error("mpv not found. Install: sudo apt-get install mpv")
            return False
        except Exception as e:
            logger.error(f"Playback error: {e}")
            return False

    def play_song_by_name(self, song_name, artist_name=""):
        try:
            search_query = f"{song_name} {artist_name}".strip()
            songs = self.search_songs(search_query, limit=1)

            if songs:
                song = songs[0]
                logger.info(f"Found: {song['title']} by {song['artist']}")
                return self.play_song_by_video_id(
                    song["video_id"], song["title"], song["artist"]
                )
            else:
                logger.warning(f"No songs found for: {search_query}")
                return False

        except Exception as e:
            logger.error(f"Error: {e}")
            return False

    def stop_playback(self):
        try:
            if self.play_process:
                self.play_process.terminate()
                self.play_process.wait()
                self.play_process = None

            os.system("pkill -f mpv 2>/dev/null")

            self.is_playing     = False
            self.current_song   = None
            self.current_artist = None
            logger.info("Playback stopped")

        except Exception as e:
            logger.error(f"Stop error: {e}")

    def is_song_playing(self):
        if self.play_process:
            return self.play_process.poll() is None
        return False

    def set_volume(self, volume):
        try:
            volume = max(0, min(100, volume))
            os.system(f"amixer set Master {volume}%")
            logger.info(f"Volume: {volume}%")
        except Exception as e:
            logger.error(f"Volume error: {e}")

    def get_current_song_info(self):
        return {
            "title":      self.current_song,
            "artist":     self.current_artist,
            "is_playing": self.is_song_playing()
        }


if __name__ == "__main__":
    print("Music Player Test")
    print("=" * 50)

    player = MusicPlayer()

    print("\n1. Searching for Kesariya...")
    songs = player.search_songs("Kesariya Arijit Singh", limit=3)

    if songs:
        print(f"\nFound: {songs[0]['title']} by {songs[0]['artist']}")
        print("\n2. Playing now...")
        player.play_song_by_video_id(
            songs[0]["video_id"],
            songs[0]["title"],
            songs[0]["artist"]
        )
        print("Playing! Press Enter to stop...")
        input()
        player.stop_playback()
        print("Stopped!")
    else:
        print("No songs found - check internet connection")
