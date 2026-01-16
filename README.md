Markdown

# 🎬 Generative Story Engine (Luxury Edition)

> **A broadcast-quality AI pipeline for cinematic storytelling.**
> *Flux Image Sequences • CogVideoX Motion • Generative Audio • 4K Upscaling*

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![PyTorch](https://img.shields.io/badge/PyTorch-2.5.1-red)
![Hardware](https://img.shields.io/badge/GPU-RTX_4060_(8GB)-green)
![Status](https://img.shields.io/badge/Status-Production--Ready-orange)

## 🎥 Demos & Results

### 1. The Full Experience (4K Video + Audio)


https://github.com/user-attachments/assets/f08df8ff-2c17-4dea-9ab4-fb8f2575226c



### 2. Flux + CogVideoX Motion
![Demo Animation](assets/demo.gif)

---

## 📖 Overview
This repository houses a modular generative AI engine designed for high-end content creation on consumer hardware. It orchestrates multiple state-of-the-art models to produce **broadcast-quality assets**.

It features a custom memory management system (`aggressive_cleanup`) that allows heavy models like **Flux.1-Schnell** and **CogVideoX-2b** to run sequentially on **8GB VRAM** without crashing.

### ✨ Key Features

#### 1. High-Fidelity Visuals (Flux 1920p)
* **Engine:** `FLUX.1-schnell`
* **Resolution:** Generates distinct keyframes at **1920x1920p** (Square/IMAX aspect) to maximize texture detail before animation.
* **Optimization:** Uses sequential CPU offloading to fit within 8GB VRAM limits.

#### 2. Cinematic Motion & 4K Upscaling
* **Motion:** `CogVideoX-2b` animates the Flux keyframes into fluid video clips (natively at 720p).
* **Upscaling:** The pipeline automatically processes the raw 720p output through **Real-ESRGAN (Vulkan)**, quadrupling the resolution to a sharp **4K (2880p/3840p)** ready for broadcast.

#### 3. Intelligent Audio Generator
A custom `AudioLDM2` implementation (`src/audio_engine.py`) that builds soundtracks intelligently:
* **Dual-Layer Synthesis:** Generates a continuous **"Theme"** layer (ambient music) and a separate **"SFX"** layer (foley/sound effects) for every scene.
* **Smart Prompting:** Automatically strips visual keywords (e.g., "4k", "camera", "lighting") from prompts so the audio model focuses purely on sound.
* **Auto-Sync:** Uses `MoviePy` to detect video duration differences. It automatically loops the audio for longer videos or trims it for shorter ones to ensure perfect synchronization.

---

## 💻 Reference Hardware
This pipeline was optimized for the following local configuration:

| Component | Specification | Performance Note |
| :--- | :--- | :--- |
| **GPU** | **NVIDIA RTX 4060** | **8GB VRAM** (Optimized with aggressive offloading) |
| **RAM** | **16GB** | Used for model weights during swapping |

---

## 🏗️ Project Structure


Generative-Story-Engine/
├── configs/            # YAML Control Centers
│   ├── flux_config.yaml
│   └── story_config.yaml
├── src/                # Core Engines
│   ├── flux_engine.py      # Flux Image Generator (1920x1920)
│   ├── video_engine.py     # CogVideoX Wrapper
│   ├── audio_engine.py     # AudioLDM2 Dual-Layer Composer
│   └── utils.py            # Memory Management
├── tools/              # Post-Processing
│   └── upscale_pipeline.py # Real-ESRGAN (Vulkan) Wrapper
├── main.py             # CLI Entry Point
└── requirements.txt    # Dependencies

🚀 Installation
1. Clone & Environment
Bash

git clone [https://github.com/danmotoc94/Generative-Story-Engine-.git](https://github.com/danmotoc94/Generative-Story-Engine-.git)
cd Generative-Story-Engine-

python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

2. Install Dependencies
Bash

pip install -r requirements.txt

3. Usage

Run the central hub to access all engines:
Bash

python main.py

    Option 1: Generate Base Images (Flux 1920p)

    Option 2: Animate Scenes (CogVideoX)

    Option 3: Upscale to 4K

    Option 4: Generate & Merge Audio

⚙️ Configuration

Video Settings (configs/story_config.yaml)
YAML

model_settings:
  model_id: "THUDM/CogVideoX-2b"
  guidance: 6.0       
  num_frames: 49      # Approx 6 seconds

Flux Settings (configs/flux_config.yaml)
YAML

video_settings:
  resolution: 1920    # 1920x1920 High-Res Output

rendering:
  model_id: "black-forest-labs/FLUX.1-schnell"
  memory_optimization: "aggressive" 

Author: Romanian Reviewer
