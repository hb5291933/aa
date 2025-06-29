import os
import whisper
import tempfile
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.VideoClip import TextClip, CompositeVideoClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.fx.all import resize, crop

# Configuration
YT_VIDEO_PATH = "yt.mp4"
TK_VIDEO_PATH = "tk.mp4"
OUTPUT_PATH = "final_outputsss.mp4"
OUTPUT_RESOLUTION = (1080, 1920)
FONT = "Arial-Bold"
FONT_SIZE = 60
TEXT_COLOR = "white"

def transcribe_to_one_word_per_second(video_path):
    print("🔊 Transcribing audio using Whisper...")
    model = whisper.load_model("base")
    
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_audio:
        audio_path = tmp_audio.name
    os.system(f'ffmpeg -y -i "{video_path}" -ar 16000 -ac 1 -f mp3 "{audio_path}"')

    result = model.transcribe(audio_path, word_timestamps=True, language="en")
    os.remove(audio_path)

    words = []
    for segment in result['segments']:
        for w in segment['words']:
            start_time = int(w['start'])  # Round down to nearest second
            word = w['word'].strip()
            if word:
                words.append((start_time, word))
    
    seen_times = set()
    one_word_per_sec = []
    for t, word in words:
        if t not in seen_times:
            one_word_per_sec.append((t, word))
            seen_times.add(t)

    print("✅ Words extracted:", one_word_per_sec[:10], "...")
    return one_word_per_sec

def combine_videos(yt_path, tk_path, subtitles):
    yt_clip = VideoFileClip(yt_path).resize(width=OUTPUT_RESOLUTION[0])
    tk_clip = VideoFileClip(tk_path).resize(width=OUTPUT_RESOLUTION[0]).without_audio()

    crop_start = int(tk_clip.h * 0.25)
    crop_end = int(tk_clip.h * 0.75)
    tk_cropped = crop(tk_clip, y1=crop_start, y2=crop_end)
    tk_resized = resize(tk_cropped, height=OUTPUT_RESOLUTION[1] // 2)

    yt_resized = resize(yt_clip, height=OUTPUT_RESOLUTION[1] // 2)
    black_top = TextClip("", size=(OUTPUT_RESOLUTION[0], OUTPUT_RESOLUTION[1] // 2), color="black", bg_color="black", print_cmd=False, method="caption").set_duration(yt_resized.duration)
    yt_padded = CompositeVideoClip([black_top.set_position("top"), yt_resized.set_position(("center", "bottom"))])

    stacked = CompositeVideoClip([
        yt_padded.set_position(("center", 0)),
        tk_resized.set_position(("center", OUTPUT_RESOLUTION[1] // 2))
    ], size=OUTPUT_RESOLUTION).set_duration(min(yt_resized.duration, tk_resized.duration))

    subtitle_clips = []
    for t, word in subtitles:
        txt = TextClip(word, fontsize=FONT_SIZE, font=FONT, color=TEXT_COLOR, bg_color="black", method="caption", size=(OUTPUT_RESOLUTION[0], None))
        txt = txt.set_position(("center", OUTPUT_RESOLUTION[1] // 2 + 100)).set_start(t).set_duration(1)
        subtitle_clips.append(txt)

    final = CompositeVideoClip([stacked] + subtitle_clips, size=OUTPUT_RESOLUTION)
    final = final.set_audio(yt_clip.audio)

    return final.set_duration(min(yt_clip.duration, tk_clip.duration))

def main():
    subtitles = transcribe_to_one_word_per_second(YT_VIDEO_PATH)
    print("🎬 Creating final video with subtitles...")
    final_clip = combine_videos(YT_VIDEO_PATH, TK_VIDEO_PATH, subtitles)
    final_clip.write_videofile(OUTPUT_PATH, fps=30, codec="libx264", audio_codec="aac")
    print("✅ Final video saved to", OUTPUT_PATH)

if __name__ == "__main__":
    main()
