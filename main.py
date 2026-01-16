import sys
import os
import subprocess
from colorama import Fore, Style, init

# Import your engines
# (Removed TurboGenerator import since you deleted the file)
from src.flux_engine import VideoSequenceGenerator
from src.video_engine import VideoStoryGenerator

# Initialize colorama for pretty text
init(autoreset=True)

def print_header():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}   🎬 GENERATIVE STORY ENGINE - RTX 4060 OPTIMIZED")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")

def main():
    while True:
        print_header()
        print(f"{Fore.YELLOW}Select an AI Engine:{Style.RESET_ALL}")
        print("1. 🖼️  High-Fidelity Sequence (Flux)")
        print("2. 🎥  Video Storytelling (CogVideoX-2b)")
        print("3. 🚀  4K Video Upscaler")
        print("4. 🎵  Generative Audio & Merge") # <--- Add this
        print("5. ❌  Exit")
        
        choice = input(f"\n{Fore.GREEN}Enter choice (1-4): {Style.RESET_ALL}")

        try:
            if choice == "1":
                print(f"\n{Fore.MAGENTA}--- Starting Flux Engine ---{Style.RESET_ALL}")
                app = VideoSequenceGenerator(config_path="configs/flux_config.yaml")
                app.run()
                input("\nPress Enter to continue...")

            elif choice == "2":
                print(f"\n{Fore.MAGENTA}--- Starting Video Story Engine ---{Style.RESET_ALL}")
                app = VideoStoryGenerator(config_path="configs/story_config.yaml")
                app.generate_and_stitch()
                input("\nPress Enter to continue...")

            elif choice == "3":
                print(f"\n{Fore.MAGENTA}--- Starting 4K Upscaler ---{Style.RESET_ALL}")
                # We run this as a subprocess because it's a standalone tool script
                subprocess.run([sys.executable, "tools/upscale_pipeline.py"])
                input("\nPress Enter to continue...")

            elif choice == '4':
                from src.audio_engine import AudioGenerator
                print(f"\n{Fore.MAGENTA}--- Starting Audio Engine ---{Style.RESET_ALL}")
                engine = AudioGenerator()
                engine.generate_audio()
                input("\nPress Enter to continue...")

           

            elif choice == "5":
                print("Goodbye!")
                sys.exit()

        except Exception as e:
            print(f"\n{Fore.RED}❌ An error occurred: {e}{Style.RESET_ALL}")
            input("Press Enter to return to menu...")

if __name__ == "__main__":
    main()