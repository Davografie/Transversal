#!/bin/bash
# Install custom node dependencies
for dir in /app/ComfyUI/custom_nodes/*; do
    if [ -f "$dir/requirements.txt" ]; then
        echo "Installing dependencies for $dir"
        pip install -r "$dir/requirements.txt"
    fi
    if [ -f "$dir/install.sh" ]; then
        echo "Running install script for $dir"
        cd "$dir" && ./install.sh && cd -
    fi
done

# Start ComfyUI
python3 main.py --listen 0.0.0.0
