from moviepy.audio.io.AudioFileClip import AudioFileClip
clip = AudioFileClip("assets/sample.mp4")
print([name for name in dir(clip) if "sub" in name.lower()])
clip.close()
