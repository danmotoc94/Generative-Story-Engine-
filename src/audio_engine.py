import torch
import yaml
import os
import soundfile as sf
import numpy as np
from diffusers import AudioLDM2Pipeline
from moviepy import VideoFileClip, AudioFileClip, concatenate_audioclips
import math

# --- 🛠️ UNIVERSAL FIX FOR AUDIO LOOPING (MoviePy v1 & v2 Compatible) 🛠️ ---
def loop_audio_clip(clip, duration):
    """Loops an audio clip to fill a specific duration."""
    n_loops = math.ceil(duration / clip.duration) + 1
    looped = concatenate_audioclips([clip] * n_loops)
    
    # Support MoviePy v2.0 (subclipped) and v1.0 (subclip)
    if hasattr(looped, 'subclipped'):
        return looped.subclipped(0, duration)
    return looped.subclip(0, duration)
# ---------------------------------------------

class AudioGenerator:
    def __init__(self, config_path="configs/story_config.yaml"):
        self.config = self.load_config(config_path)
        self.prompts = self.config['prompts']
        # Load audio settings with defaults
        self.audio_settings = self.config.get('audio_settings', {
            'theme_prompt': "Cinematic ambient music",
            'theme_volume': 0.4,
            'sfx_volume': 1.0,
            'negative_prompt': "low quality, noise"
        })
        
        self.output_dir = "outputs/audio_tracks"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # VISUAL CLEANER: Words we don't want triggering sounds
        self.banned_words = [
            "drone", "shot", "camera", "4k", "8k", "photorealistic", 
            "vivid", "colors", "lighting", "depth of field", "slow motion"
        ]

    def load_config(self, path):
        with open(path, 'r') as f:
            return yaml.safe_load(f)

    def clean_prompt_for_audio(self, text):
        """Removes visual terms so we don't generate camera motors or static."""
        text = text.lower()
        for word in self.banned_words:
            text = text.replace(word, "")
        return " ".join(text.split())

    def generate_audio(self):
        print("\n🎵 AUDIO ENGINE V2 (AudioLDM2 Dual-Layer)")
        print("------------------------------------------")
        
        # 1. LOAD MODEL
        model_id = "cvssp/audioldm2"
        print(f"   🧠 Loading High-Fidelity Model: {model_id}...")
        
        try:
            pipe = AudioLDM2Pipeline.from_pretrained(model_id, torch_dtype=torch.float16)
            pipe = pipe.to("cuda")
        except Exception as e:
            print(f"   ❌ Failed to load model: {e}")
            return None
        
        sample_rate = 16000
        
        # Calculate Duration
        SCENE_DURATION = 6.0 
        total_duration = len(self.prompts) * SCENE_DURATION
        print(f"   ⏱️  Total Soundtrack Duration: {total_duration}s")

        # --- LAYER 1: THEME MUSIC ---
        print(f"   🎻 Generating Theme Layer...")
        theme_prompt = self.audio_settings['theme_prompt']
        
        theme_audio_segments = []
        remaining_time = total_duration
        
        while remaining_time > 0:
            segment_len = min(remaining_time, 10.0) 
            music_result = pipe(
                theme_prompt,
                negative_prompt=self.audio_settings['negative_prompt'],
                num_inference_steps=25,
                audio_length_in_s=segment_len,
                num_waveforms_per_prompt=1
            )
            audio_data = music_result.audios[0]
            if isinstance(audio_data, torch.Tensor): audio_data = audio_data.cpu().numpy()
            theme_audio_segments.append(audio_data.flatten())
            remaining_time -= segment_len
            
        full_theme = np.concatenate(theme_audio_segments)
        
        # --- LAYER 2: SCENE FOLEY (SFX) ---
        print(f"   🌊 Generating SFX Layer for {len(self.prompts)} scenes...")
        sfx_segments = []
        
        for i, prompt_entry in enumerate(self.prompts):
            raw_text = prompt_entry if isinstance(prompt_entry, str) else prompt_entry.get('prompt', '')
            if not raw_text: continue
            
            audio_text = self.clean_prompt_for_audio(raw_text)
            final_prompt = f"High fidelity sound effect of {audio_text}, realistic, field recording"
            
            print(f"      ▶ Scene {i+1} SFX: '{audio_text[:30]}...'")
            
            sfx_result = pipe(
                final_prompt,
                negative_prompt=self.audio_settings['negative_prompt'],
                num_inference_steps=20,
                audio_length_in_s=SCENE_DURATION
            )
            
            audio_data = sfx_result.audios[0]
            if isinstance(audio_data, torch.Tensor): audio_data = audio_data.cpu().numpy()
            sfx_segments.append(audio_data.flatten())

        full_sfx = np.concatenate(sfx_segments)

        # --- LAYER 3: MIXING ---
        print("   🎚️  Mixing Tracks...")
        
        min_len = min(len(full_theme), len(full_sfx))
        full_theme = full_theme[:min_len]
        full_sfx = full_sfx[:min_len]
        
        vol_theme = self.audio_settings['theme_volume']
        vol_sfx = self.audio_settings['sfx_volume']
        
        mixed_audio = (full_theme * vol_theme) + (full_sfx * vol_sfx)
        
        max_val = np.max(np.abs(mixed_audio))
        if max_val > 0:
            mixed_audio = mixed_audio / max_val
            
        base_filename = self.config['model_settings']['output_filename']
        audio_filename = base_filename.replace(".mp4", "_MASTER_AUDIO.wav")
        final_audio_path = os.path.join(self.output_dir, audio_filename)
        
        sf.write(final_audio_path, mixed_audio, sample_rate)
        print(f"   🏆 Master Audio Saved: {final_audio_path}")
        
        self.merge_with_video(final_audio_path)
        return final_audio_path
    
    def merge_with_video(self, audio_path):
        print("\n🎬 MERGING VIDEO + AUDIO")
        print("---------------------------")
        
        base_filename = self.config['model_settings']['output_filename']
        
        candidates = [
            (os.path.join("outputs", "upscaled_videos", base_filename.replace(".mp4", "_REAL_4K.mp4")), "outputs/upscaled_videos"),
            (os.path.join("outputs", "story_videos", base_filename), "outputs/story_videos"),
            (os.path.join("outputs", base_filename), "outputs")
        ]
        
        video_path = None
        output_folder = ""
        
        for path, folder in candidates:
            if os.path.exists(path):
                video_path = path
                output_folder = folder
                print(f"   📼 Found Video Source: {path}")
                break
        
        if not video_path:
            print(f"   ❌ Could not find any video file for {base_filename}")
            return None

        output_filename = os.path.basename(video_path).replace(".mp4", "_WITH_AUDIO.mp4")
        output_path = os.path.join(output_folder, output_filename)
        
        try:
            video = VideoFileClip(video_path)
            audio = AudioFileClip(audio_path)
            
            # --- 🧠 SMART AUDIO SYNC ---
            # If video is significantly longer (> 2s), we loop (it's probably intentional background music).
            # If video is barely longer (framerate drift), we just accept the silence at the end.
            
            duration_diff = video.duration - audio.duration
            
            if duration_diff > 2.0:
                print(f"   🔁 Video is {duration_diff:.2f}s longer. Looping audio...")
                audio = loop_audio_clip(audio, video.duration)
            elif duration_diff > 0:
                print(f"   🤏 Video is slightly longer ({duration_diff:.2f}s). Padding with silence (No Loop).")
                # We don't loop. MoviePy will just play silence for the last fraction of a second.
                # Just ensure we don't cut the video short.
            else:
                # Audio is longer than video; trim audio
                print(f"   ✂️  Trimming audio to match video...")
                if hasattr(audio, 'subclipped'):
                    audio = audio.subclipped(0, video.duration)
                else:
                    audio = audio.subclip(0, video.duration)
            
            # Apply audio
            if hasattr(video, 'with_audio'):
                final_video = video.with_audio(audio)
            else:
                final_video = video.set_audio(audio)
            
            print(f"   💾 Encoding final video...")
            final_video.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                fps=video.fps,
                logger=None 
            )
            
            video.close()
            audio.close()
            final_video.close()
            
            print(f"\n   ✅ DONE: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"   ❌ Merge Error: {e}")
            import traceback
            traceback.print_exc()
            return None

if __name__ == "__main__":
    gen = AudioGenerator()
    gen.generate_audio()