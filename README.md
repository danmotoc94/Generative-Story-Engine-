# 🎬 Generative Story Engine (Luxury Edition)

> **A broadcast-quality AI pipeline for cinematic storytelling.**
> *Flux Image Sequences • CogVideoX Motion • Generative Audio • 4K Upscaling*

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![PyTorch](https://img.shields.io/badge/PyTorch-2.5.1-red)
![Hardware](https://img.shields.io/badge/GPU-RTX_4060_(8GB)-green)
![Status](https://img.shields.io/badge/Status-Production--Ready-orange)

## 🎥 Demos & Results

### 1. The Full Experience (4K Video + Audio)


Uploading demo_small.mp4…



### 2. Flux + CogVideoX Motion
![Demo Animation](assets/demo.gif)

---

## 📖 Overview
This repository houses a modular generative AI engine designed for high-end content creation on consumer hardware. It orchestrates multiple state-of-the-art models to produce **broadcast-quality assets**.

It features a custom memory management system (`aggressive_cleanup`) that allows heavy models like **Flux.1-Schnell** and **CogVideoX-2b** to run sequentially on **8GB VRAM** without crashing.

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
│   ├── flux_engine.py      # Image Sequence Generator
│   ├── video_engine.py     # CogVideoX Wrapper
│   ├── audio_engine.py     # AudioLDM2 Composer
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

    Option 1: Generate Base Images (Flux)

    Option 2: Animate Scenes (CogVideoX)

    Option 3: Upscale to 4K

    Option 4: Generate & Merge Audio

⚙️ Configuration

Video Settings (configs/story_config.yaml)
YAML

model_settings:
  model_id: "THUDM/CogVideoX-2b"
  guidance: 6.0       # Higher = follows prompt strictly
  num_frames: 49      # Approx 6 seconds

Flux Settings (configs/flux_config.yaml)
YAML

rendering:
  model_id: "black-forest-labs/FLUX.1-schnell"
  memory_optimization: "aggressive" # Essential for 8GB cards
transitions:
  style: "smooth"

Author: Dan Motoc
