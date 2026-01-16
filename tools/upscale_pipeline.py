import os
import subprocess
import requests
import shutil
import stat
import imageio
from PIL import Image

class VideoUpscaler:
    def __init__(self):
        self.output_dir = "outputs/upscaled_videos"
        self.bin_dir = "bin"
        self.temp_dir = "outputs/temp_frames"
        self.upscaled_temp_dir = "outputs/temp_frames_hd"
        
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.bin_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.upscaled_temp_dir, exist_ok=True)
        
        # Linux Binary URL for Real-ESRGAN
        self.binary_url = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-ubuntu.zip"
        self.binary_path = os.path.join(self.bin_dir, "realesrgan-ncnn-vulkan")

    def download_binary(self):
        if os.path.exists(self.binary_path):
            return

        print("⬇️  Downloading Real-ESRGAN Binary (This happens once)...")
        zip_path = os.path.join(self.bin_dir, "realesrgan.zip")
        
        # Download
        try:
            response = requests.get(self.binary_url, stream=True)
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Unzip
            import zipfile
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.bin_dir)
            
            # Cleanup & Permission
            os.remove(zip_path)
            st = os.stat(self.binary_path)
            os.chmod(self.binary_path, st.st_mode | stat.S_IEXEC)
            print("✅ Binary installed successfully.")
            
        except Exception as e:
            print(f"❌ Failed to download binary: {e}")

    def upscale_video(self):
        print("\n🚀 REAL-ESRGAN UPSCALER (Sharp 4K)")
        print("--------------------------------")
        
        # 0. SETUP
        self.download_binary()
        if not os.path.exists(self.binary_path):
            print("❌ Error: Binary not found.")
            return

        # 1. INPUT
        default_path = "outputs/story_videos/story_output_NATURE_BRIGHT.mp4"
        input_path = input(f"Enter video path (default: {default_path}): ").strip()
        if not input_path: input_path = default_path
        
        if not os.path.exists(input_path):
            print(f"❌ File not found.")
            return

        # 2. EXTRACT FRAMES
        print("   📂 Extracting frames...")
        reader = imageio.get_reader(input_path)
        fps = reader.get_meta_data().get('fps', 8)
        
        # Clear temp dirs
        for f in os.listdir(self.temp_dir): os.remove(os.path.join(self.temp_dir, f))
        for f in os.listdir(self.upscaled_temp_dir): os.remove(os.path.join(self.upscaled_temp_dir, f))

        for i, frame in enumerate(reader):
            imageio.imwrite(os.path.join(self.temp_dir, f"frame_{i:05d}.png"), frame)
        reader.close()

        # 3. RUN REAL-ESRGAN
        # -s 4: Scale 4x (720p -> 2880p)
        # -n: Model name (realesrgan-x4plus is best for nature)
        print("   ⚡ Upscaling with Vulkan (This is fast)...")
        cmd = [
            self.binary_path,
            "-i", self.temp_dir,
            "-o", self.upscaled_temp_dir,
            "-s", "4",
            "-n", "realesrgan-x4plus" 
        ]
        
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ Upscale failed: {e}")
            return

        # 4. STITCH
        print(f"   🧵 Stitching back to video at {fps} FPS...")
        output_filename = os.path.basename(input_path).replace(".mp4", "_REAL_4K.mp4")
        output_path = os.path.join(self.output_dir, output_filename)

        # Re-read frames from the HD folder
        frame_files = sorted(os.listdir(self.upscaled_temp_dir))
        if not frame_files:
            print("❌ No upscaled frames found.")
            return
            
        # Use ffmpeg for stitching (better quality than imageio for 4K)
        # We need to construct a file list or pattern
        # Easier: Use imageio to write mp4 directly if ffmpeg is complex to call
        
        writer = imageio.get_writer(output_path, fps=fps, macro_block_size=8)
        for filename in frame_files:
            file_path = os.path.join(self.upscaled_temp_dir, filename)
            frame = imageio.imread(file_path)
            writer.append_data(frame)
        writer.close()

        print(f"   🏆 SUCCESS! Sharp 4K video saved:\n   -> {output_path}")

        # Cleanup
        # shutil.rmtree(self.temp_dir)
        # shutil.rmtree(self.upscaled_temp_dir)

if __name__ == "__main__":
    upscaler = VideoUpscaler()
    upscaler.upscale_video()