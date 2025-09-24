# For NVIDIA GPUs
FROM nvidia/cuda:12.4.1-base-ubuntu22.04

# Install Python and dependencies
RUN apt-get update && apt-get install -y python3 python3-pip git
RUN pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu129

# Clone and set up ComfyUI
RUN git clone https://github.com/comfyanonymous/ComfyUI.git /app/ComfyUI
WORKDIR /app/ComfyUI
RUN pip install -r requirements.txt

# Install x-flux-comfyui
WORKDIR /app/ComfyUI/custom_nodes
RUN git clone https://github.com/XLabs-AI/x-flux-comfyui.git x-flux-comfyui
WORKDIR /app/ComfyUI/custom_nodes/x-flux-comfyui
RUN python3 setup.py

# Install ComfyUI-Custom-Scripts
WORKDIR /app/ComfyUI/custom_nodes
RUN git clone https://github.com/pythongosssss/ComfyUI-Custom-Scripts.git ComfyUI-Custom-Scripts

# Install ComfyUI-Lora-Auto-Trigger-Words
WORKDIR /app/ComfyUI/custom_nodes
RUN git clone https://github.com/idrirap/ComfyUI-Lora-Auto-Trigger-Words.git ComfyUI-Lora-Auto-Trigger-Words

# Install WASAS-node-suite-ComfyUI
WORKDIR /app/ComfyUI/custom_nodes
RUN git clone https://github.com/WASASquatch/was-node-suite-comfyui.git was-node-suite-comfyui
WORKDIR /app/ComfyUI/custom_nodes/was-node-suite-comfyui
RUN pip install -r requirements.txt

# Install ComfyUI_Comfyroll_CustomNodes
WORKDIR /app/ComfyUI/custom_nodes
RUN git clone https://github.com/Suzie1/ComfyUI_Comfyroll_CustomNodes ComfyUI_Comfyroll_CustomNodes

# Install ComfyUI-GGUF
WORKDIR /app/ComfyUI/custom_nodes
RUN git clone https://github.com/city96/ComfyUI-GGUF ComfyUI-GGUF

WORKDIR /app/ComfyUI

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]

# Run ComfyUI
CMD ["python3", "main.py", "--listen"]
