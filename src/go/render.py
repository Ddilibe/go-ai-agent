#!/usr/bin/env python3
import os
from enum import StrEnum

from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageSequenceClip, AudioFileClip, concatenate_audioclips

from .board import Board
from .exceptions import MusicFileNotFoundError


class AudioMode(StrEnum):
    LOOP = "loop"
    FADE = "fade"
    SILENCE = "silence"
    NONE = "none"


def render_board(board: Board, step: int, move, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    size = board.size
    cell = 40
    margin = 20
    img_size = size * cell + 2 * margin

    img = Image.new("RGB", (img_size, img_size), (230, 180, 100))
    draw = ImageDraw.Draw(img)

    # Draw grid
    for i in range(size):
        xy = margin + i * cell
        draw.line([(margin, xy), (img_size - margin, xy)], fill="black")
        draw.line([(xy, margin), (xy, img_size - margin)], fill="black")

    # Draw stones
    for r in range(size):
        for c in range(size):
            v = board.grid[r, c]
            if v == 0:
                continue
            color = (0, 0, 0) if v == 1 else (255, 255, 255)
            x = margin + c * cell
            y = margin + r * cell
            draw.ellipse(
                [
                    (x - cell / 2 + 2, y - cell / 2 + 2),
                    (x + cell / 2 - 2, y + cell / 2 - 2),
                ],
                fill=color,
                outline="black",
            )

    # Annotate move number
    if move:
        r, c = move
        x = margin + c * cell
        y = margin + r * cell
        draw.ellipse(
            [(x - 5, y - 5), (x + 5, y + 5)],
            fill=(255, 0, 0),
            outline="black",
        )

    img.save(os.path.join(output_dir, f"step_{step:04d}.png"))


def render_video(
    images_dir: str = "cache",
    audio_file: str = "",
    fps=1,
    audio_mode: AudioMode = AudioMode.NONE,
) -> None:
    """
    Create a replay video from Go board snapshots.
        - images_dir: directory with PNGs
        - audio_file: Optional MP3 file path
        - fps: Frames persecond with default 1
        - audio mode:
            * 'loop' -> Repeat music until video ends
            * 'fade' -> Fade out music when it stops
            * 'silence' -> Play once, then silence
            * 'None' -> Play no music at all
    """

    os.makedirs("videos", exist_ok=True)

    frames = sorted(
        [
            os.path.join(images_dir, f)
            for f in os.listdir(images_dir)
            if f.endswith(".png")
        ]
    )
    if not frames:
        raise FileNotFoundError("No Image frames found in the cache directory")

    clip = ImageSequenceClip(frames, fps=fps)

    if not os.path.exists(audio_file):
        raise MusicFileNotFoundError(audio_file)
    audio = AudioFileClip(audio_file).subclip(0, clip.duration)
    
    output_path = f"videos/{images_dir.split("/")[-2]}.mp4"
    if os.path.exists(audio_file):
        print(f"🎵 Adding background music: {audio_file}")
        audio = AudioFileClip(audio_file)

        if audio.duration < clip.duration:
            loops = int(clip.duration // audio.duration) + 1
            final_audio = concatenate_audioclips([audio] * loops).subclip(0, clip.duration) # type: ignore
        else:
            final_audio = audio.subclip(0, clip.duration)

        clip = clip.set_audio(final_audio)
    else:
        print("⚠️ Audio file not found. Proceeding without music.")

    # Step 4: Export video
    print(f"📀 Exporting video to {output_path} ...")
    if clip:
        clip.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=fps)
        print("✅ Video created successfully!") 
        return

    print(f"❌ Error Saving {output_path}")
    return
