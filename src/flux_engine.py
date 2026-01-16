import os
import sys
import yaml
import torch
import gc
from PIL import Image, ImageDraw
from diffusers import FluxPipeline
from datetime import datetime

# --- HELPER: Memory Cleanup ---
def aggressive_cleanup():
    """Forces garbage collection and clears CUDA cache."""
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()

# --- CONSTANTS ---
BASE_ARTISTIC_STYLE = """
Cinematic composition, photorealistic, hyper-realistic textures, extreme sharpness, 
atmospheric depth, masterpiece quality. Shot on high-end cinema camera, 85mm lens, 
f/1.8, shallow depth of field, professional color grading, HDR.
"""

class VideoSequenceGenerator:
    def __init__(self, config_path=None):
        print("🔧 Initializing Generator...")
        
        # 1. Path Management
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_root = os.path.dirname(self.script_dir)
        
        # FIX: Handle the config_path argument from the menu
        if config_path is None:
            # Default location
            self.config_path = os.path.join(self.project_root, "configs", "flux_config.yaml")
        else:
            # Use provided path (ensuring it's absolute)
            if not os.path.isabs(config_path):
                self.config_path = os.path.join(self.project_root, config_path)
            else:
                self.config_path = config_path
        
        # 2. Load Config
        self.config = self.load_config(self.config_path)
        self.video_settings = self.config['video_settings']
        self.scenes = self.config['scenes']
        self.transitions = self.config['transitions']
        self.rendering = self.config['rendering']
        self.output_settings = self.config['output']
        
        self.total_frames = self.calculate_total_frames()
        
        # 3. Setup Output Folders
        output_folder_name = self.video_settings.get('output_directory', 'outputs/flux_frames')
        if not os.path.isabs(output_folder_name):
            self.output_dir = os.path.join(self.project_root, output_folder_name)
        else:
            self.output_dir = output_folder_name
            
        self.setup_directories()
        self.pipeline = None
        
    def load_config(self, config_path):
        if not os.path.exists(config_path):
            print(f"❌ Config file not found at: {config_path}")
            sys.exit(1)
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            sys.exit(1)

    def calculate_total_frames(self):
        total = sum(scene.get('duration_frames', 5) for scene in self.scenes)
        if 'total_frames' in self.video_settings:
            limit = self.video_settings['total_frames']
            print(f"⚠️ Limit applied: Generating {limit} frames out of {total} total.")
            return min(total, limit)
        return total
    
    def setup_directories(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_dir = os.path.join(self.output_dir, f"run_{timestamp}")
        
        self.dirs = {
            'raw': os.path.join(self.run_dir, "raw"),
            'processed': os.path.join(self.run_dir, "processed"),
        }
        
        os.makedirs(self.dirs['processed'], exist_ok=True)
        if self.output_settings.get('keep_raw_frames', False):
            os.makedirs(self.dirs['raw'], exist_ok=True)
        
        print(f"📁 Output directory: {self.run_dir}")
    
    def get_scene_data(self, scene_name):
        for scene in self.scenes:
            if scene['name'] == scene_name:
                return scene
        return None

    def generate_scene_prompt(self, scene_name, frame_idx, total_in_scene):
        scene = self.get_scene_data(scene_name)
        if not scene: return "Cinematic nature scene"
        
        base_desc = scene['description']
        keywords = ", ".join(scene.get('keywords', []))
        
        progression = ""
        if total_in_scene > 1:
            progress = frame_idx / total_in_scene
            if progress < 0.2: progression = "Establishing wide shot. "
            elif progress < 0.8: progression = "Medium detail shot. "
            else: progression = "Slow push in, intense focus. "
        
        return f"{progression}{base_desc}. Elements: {keywords}. {BASE_ARTISTIC_STYLE}"
    
    def generate_transition_prompt(self, scene_a_name, scene_b_name, progress):
        scene_a = self.get_scene_data(scene_a_name)
        scene_b = self.get_scene_data(scene_b_name)
        desc_a = scene_a['description'] if scene_a else scene_a_name
        desc_b = scene_b['description'] if scene_b else scene_b_name

        if self.transitions['style'] == 'morph':
            return f"CINEMATIC TRANSITION: {desc_a} morphing into {desc_b}. Double exposure. {BASE_ARTISTIC_STYLE}"
        else:
            if progress < 0.5: return f"{desc_a} fading out. {BASE_ARTISTIC_STYLE}"
            else: return f"{desc_b} fading in. {BASE_ARTISTIC_STYLE}"

    def get_frame_info(self, frame_idx):
        current_frame = 0
        requested_trans = self.transitions.get('duration_frames', 4)

        for scene_idx, scene in enumerate(self.scenes):
            scene_frames = scene.get('duration_frames', 5)
            
            # --- SAFETY FIX: Clamp transition duration ---
            effective_trans = min(requested_trans, max(0, scene_frames - 1))
            main_scene_len = scene_frames - effective_trans
            
            # 1. Main Scene Part
            if frame_idx < current_frame + main_scene_len:
                return {
                    'type': 'scene',
                    'scene': scene['name'],
                    'next_scene': self.scenes[(scene_idx + 1) % len(self.scenes)]['name'],
                    'progress': (frame_idx - current_frame) / max(1, main_scene_len),
                    'is_transition': False,
                    'local_idx': frame_idx - current_frame,
                    'scene_len': main_scene_len
                }
            
            # 2. Transition Part
            elif frame_idx < current_frame + scene_frames:
                transition_start = current_frame + main_scene_len
                next_scene_idx = (scene_idx + 1) % len(self.scenes)
                return {
                    'type': 'transition',
                    'scene': scene['name'],
                    'next_scene': self.scenes[next_scene_idx]['name'],
                    'progress': (frame_idx - transition_start) / max(1, effective_trans),
                    'is_transition': True
                }
            
            current_frame += scene_frames
        
        # Fallback
        return {
            'type': 'scene',
            'scene': self.scenes[-1]['name'],
            'next_scene': self.scenes[0]['name'],
            'progress': 1.0,
            'is_transition': False,
            'local_idx': 0,
            'scene_len': 1
        }
    
    def generate_seed(self, frame_idx):
        base = self.rendering.get('base_seed', 42)
        var = self.rendering.get('seed_variation', 50)
        return base + (frame_idx * 73) % var
    
    def initialize_pipeline(self):
        print(f"🚀 Loading Model: {self.rendering['model_id']}...")
        aggressive_cleanup()
        
        os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:256,expandable_segments:True'
        
        self.pipeline = FluxPipeline.from_pretrained(
            self.rendering['model_id'],
            torch_dtype=torch.bfloat16
        )
        
        if self.rendering.get('memory_optimization') == 'aggressive':
            self.pipeline.enable_sequential_cpu_offload()
        else:
            self.pipeline.enable_model_cpu_offload()
            
        self.pipeline.vae.enable_tiling()
        self.pipeline.vae.enable_slicing()
        print("✅ Pipeline initialized successfully")

    def create_gif(self):
        print("\n🎞️  Assembling GIF...")
        source_dir = self.dirs['processed']
        
        frame_files = sorted(
            [os.path.join(source_dir, f) for f in os.listdir(source_dir) if f.endswith('.png')]
        )
        
        if not frame_files:
            print("❌ No frames found to create GIF.")
            return

        frames = [Image.open(f) for f in frame_files]
        fps = self.video_settings.get('fps', 3)
        duration_ms = int(1000 / fps)
        
        gif_path = os.path.join(self.run_dir, "animation.gif")
        
        try:
            frames[0].save(
                gif_path, format="GIF", append_images=frames[1:],
                save_all=True, duration=duration_ms, loop=0, optimize=False
            )
            print(f"✅ GIF created successfully: {gif_path}")
        except Exception as e:
            print(f"❌ GIF creation failed: {e}")

    def run(self):
        print(f"\n🎬 STARTING GENERATION: {self.total_frames} Frames")
        self.initialize_pipeline()
        
        for frame_idx in range(self.total_frames):
            aggressive_cleanup()
            
            frame_info = self.get_frame_info(frame_idx)
            
            if frame_info['is_transition']:
                prompt = self.generate_transition_prompt(
                    frame_info['scene'], frame_info['next_scene'], frame_info['progress']
                )
            else:
                prompt = self.generate_scene_prompt(
                    frame_info['scene'], frame_info['local_idx'], frame_info['scene_len']
                )
            
            seed = self.generate_seed(frame_idx)
            res = self.video_settings['resolution']
            
            print(f"🎨 Frame {frame_idx+1}/{self.total_frames} | {frame_info['scene']} [{'Trans' if frame_info['is_transition'] else 'Main'}]")
            
            try:
                # 1. Generate Image
                image = self.pipeline(
                    prompt=prompt,
                    num_inference_steps=self.rendering['num_steps'],
                    guidance_scale=0.0,
                    height=res,
                    width=res,
                    generator=torch.Generator("cpu").manual_seed(seed)
                ).images[0]
                
                # 2. Save RAW (Clean) if requested
                if self.output_settings.get('keep_raw_frames', False):
                    raw_filename = os.path.join(self.dirs['raw'], f"frame_{frame_idx:03d}.png")
                    image.save(raw_filename)

                # 3. Add Labels
                if self.output_settings.get('add_frame_labels', False):
                    draw = ImageDraw.Draw(image)
                    draw.rectangle([10, res-40, 300, res-10], fill="black")
                    draw.text((20, res-35), f"F{frame_idx} | {frame_info['scene']}", fill="white")
                
                # 4. Save PROCESSED (Labeled)
                filename = os.path.join(self.dirs['processed'], f"frame_{frame_idx:03d}.png")
                image.save(filename)
                
            except Exception as e:
                print(f"❌ Frame {frame_idx} failed: {e}")
                
        del self.pipeline
        aggressive_cleanup()

        if self.output_settings.get('create_gif', False):
            self.create_gif()
        
        print(f"\n✨ Run Complete! Check output in: {self.run_dir}")

if __name__ == "__main__":
    generator = VideoSequenceGenerator()
    generator.run()