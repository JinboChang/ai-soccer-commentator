from pathlib import Path
path = Path(r"C:\Users\jjb08\AppData\Local\Programs\Python\Python311\Lib\site-packages\moviepy\Clip.py")
lines = path.read_text().splitlines()
for i in range(360, 430):
    print(f"{i+1}: {lines[i]}")
