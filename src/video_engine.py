import torch
import yaml
import os
import subprocess
import random
import gc
import numpy as np
import imageio
from diffusers import DiffusionPipeline, CogVideoXPipeline, DPMSolverMultistepScheduler

# --- ROBUST SAVING FUNCTION ---
def save_video_frames(frames, filename, fps=8):
    """
    Manually saves frames using imageio to avoid diffusers library bugs.
    Handles PIL Images (CogVideo) or Numpy Arrays (Zeroscope).
    """
    print(f"   💾 Saving video to {filename}...")
    try:
        # Convert PIL images to Numpy if needed
        if isinstance(frames[0], object) and hasattr(frames[0], "save"):
            # It's a PIL Image (CogVideoX)
            video_data = [np.array(frame) for frame in frames]
        else:
            # It's already numpy/tensor (Zeroscope)
            video_data = frames

        # Write the video file directly
        imageio.mimwrite(filename, video_data, fps=fps, quality=9)
        print(f"   ✅ Success! Saved {filename}")
    except Exception as e:
        print(f"   ❌ Failed to save video: {e}")

def aggressive_cleanup():
    gc.collect()
    torch.cuda.empty_cache()
    if torch.cuda.is_available():
        torch.cuda.synchronize()

class VideoStoryGenerator:
    def __init__(self, config_path="configs/story_config.yaml"):
        self.config = self.load_config(config_path)
        self.settings = self.config['model_settings']
        self.story = self.config['story_settings']
        self.prompts = self.config['prompts']
        os.makedirs("outputs/temp_clips", exist_ok=True)
        os.makedirs("outputs/story_videos", exist_ok=True)

    def load_config(self, path):
        with open(path, 'r') as f:
            return yaml.safe_load(f)

    def generate_and_stitch(self):
        print(f"🚀 Starting Story Generation ({len(self.prompts)} scenes)...")
        aggressive_cleanup()

        model_id = self.settings['model_id']
        print(f"   Loading Model: {model_id} (Low VRAM Mode)...")
        
        # 1. SMART MODEL LOADING
        if "CogVideoX" in model_id:
            pipe = CogVideoXPipeline.from_pretrained(model_id, torch_dtype=torch.float16)
            is_modern = True
        else:
            pipe = DiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float16)
            pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
            is_modern = False

        # LAPTOP SAFETY SETTINGS
        pipe.enable_sequential_cpu_offload()
        if hasattr(pipe, "vae"):
            pipe.vae.enable_slicing()
            pipe.vae.enable_tiling()

        clip_filenames = []
        base_style = self.story['base_style']
        start_seed = random.randint(0, 999999)

        # 2. GENERATION LOOP
        for i, prompt_text in enumerate(self.prompts):
            print(f"\n🎬 Generating Scene {i+1}/{len(self.prompts)}...")
            full_prompt = f"{prompt_text}, {base_style}"
            
            if self.story['seed_mode'] == 'continuous':
                seed = start_seed + i
            else:
                seed = random.randint(0, 999999)
            generator = torch.manual_seed(seed)

            try:
                if is_modern:
                    # CogVideoX
                    frames = pipe(
                        prompt=full_prompt,
                        num_frames=self.settings['num_frames'],
                        guidance_scale=self.settings['guidance'],
                        num_inference_steps=self.settings['steps'],
                        generator=generator
                    ).frames[0]
                else:
                    # Zeroscope
                    frames = pipe(
                        prompt=full_prompt,
                        height=self.settings['height'],
                        width=self.settings['width'],
                        num_inference_steps=self.settings['steps'],
                        guidance_scale=self.settings['guidance'],
                        num_frames=self.settings['num_frames'],
                        generator=generator
                    ).frames[0]

                # USE THE NEW ROBUST SAVE FUNCTION
                filename = f"outputs/temp_clips/clip_{i:03d}.mp4"
                save_video_frames(frames, filename, fps=self.settings['fps'])
                clip_filenames.append(filename)
            
            except Exception as e:
                print(f"❌ Error in generation loop: {e}")
                continue
            
            aggressive_cleanup()

        del pipe
        aggressive_cleanup()

        if clip_filenames:
            self.stitch_videos(clip_filenames)

    def stitch_videos(self, clip_filenames):
        print("\n🧵 Stitching Story...")
        output_path = os.path.join("outputs/story_videos", self.settings['output_filename'])
        
        # Build filter complex for crossfades
        if len(clip_filenames) < 2:
            print("⚠️ Not enough clips to stitch. Copying single file.")
            import shutil
            shutil.copy(clip_filenames[0], output_path)
            print(f"✅ COMPLETE: {output_path}")
            return

        # Simple concat approach for CogVideo (safer than complex filters)
        with open("file_list.txt", "w") as f:
            for filename in clip_filenames:
                f.write(f"file '{os.path.abspath(filename)}'\n")
        
        cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", "file_list.txt", "-c", "copy", output_path
        ]
        
        try:
            subprocess.run(cmd, check=True)
            print(f"\n✅ STORY COMPLETE: {output_path}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Stitching Error: {e}")
            
        if os.path.exists("file_list.txt"): os.remove("file_list.txt")

if __name__ == "__main__":
    gen = VideoStoryGenerator()
    gen.generate_and_stitch()