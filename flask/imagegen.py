import json
from urllib import request
import random
import os


prompt_text = """
{
  "3": {
    "inputs": {
      "noise_seed": 257762932021983,
      "steps": 24,
      "timestep_to_start_cfg": 1,
      "true_gs": 3.5,
      "image_to_image_strength": 0,
      "denoise_strength": 1,
      "model": [
        "30",
        0
      ],
      "conditioning": [
        "5",
        0
      ],
      "neg_conditioning": [
        "19",
        0
      ],
      "latent_image": [
        "24",
        4
      ]
    },
    "class_type": "XlabsSampler",
    "_meta": {
      "title": "Xlabs Sampler"
    }
  },
  "4": {
    "inputs": {
      "clip_name1": "flux/Long-ViT-L-14-BEST-GmP-smooth-ft.safetensors",
      "clip_name2": "flux/flan_t5_xxl_full_FP8e4m3.safetensors",
      "type": "flux",
      "device": "default"
    },
    "class_type": "DualCLIPLoader",
    "_meta": {
      "title": "DualCLIPLoader"
    }
  },
  "5": {
    "inputs": {
      "clip_l": [
        "25",
        0
      ],
      "t5xxl": [
        "25",
        0
      ],
      "guidance": 3.5,
      "clip": [
        "30",
        1
      ]
    },
    "class_type": "CLIPTextEncodeFlux",
    "_meta": {
      "title": "CLIPTextEncodeFlux"
    }
  },
  "7": {
    "inputs": {
      "samples": [
        "3",
        0
      ],
      "vae": [
        "8",
        0
      ]
    },
    "class_type": "VAEDecode",
    "_meta": {
      "title": "VAE Decode"
    }
  },
  "8": {
    "inputs": {
      "vae_name": "flux/ae.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "19": {
    "inputs": {
      "clip_l": [
        "26",
        0
      ],
      "t5xxl": [
        "26",
        0
      ],
      "guidance": 4,
      "clip": [
        "4",
        0
      ]
    },
    "class_type": "CLIPTextEncodeFlux",
    "_meta": {
      "title": "CLIPTextEncodeFlux"
    }
  },
  "24": {
    "inputs": {
      "width": 1024,
      "height": 1024,
      "aspect_ratio": "custom",
      "swap_dimensions": "Off",
      "upscale_factor": 1,
      "batch_size": 1
    },
    "class_type": "CR SDXL Aspect Ratio",
    "_meta": {
      "title": "🔳 CR SDXL Aspect Ratio"
    }
  },
  "25": {
    "inputs": {
      "text": "concept art of a vertical spaceship, thrusters, hull, in outer space"
    },
    "class_type": "Text Multiline",
    "_meta": {
      "title": "positive"
    }
  },
  "26": {
    "inputs": {
      "text": "spacestation"
    },
    "class_type": "Text Multiline",
    "_meta": {
      "title": "negative"
    }
  },
  "27": {
    "inputs": {
      "unet_name": "fluxArtFusionFP16_v10Q8.gguf"
    },
    "class_type": "UnetLoaderGGUF",
    "_meta": {
      "title": "Unet Loader (GGUF)"
    }
  },
  "28": {
    "inputs": {
      "output_path": "[time(%Y-%m-%d)]",
      "filename_prefix": "ComfyUI",
      "filename_delimiter": "_",
      "filename_number_padding": 4,
      "filename_number_start": "false",
      "extension": "png",
      "dpi": 300,
      "quality": 100,
      "optimize_image": "true",
      "lossless_webp": "false",
      "overwrite_mode": "false",
      "show_history": "false",
      "show_history_by_prefix": "true",
      "embed_workflow": "false",
      "show_previews": "false",
      "images": [
        "7",
        0
      ]
    },
    "class_type": "Image Save",
    "_meta": {
      "title": "Image Save"
    }
  },
  "29": {
    "inputs": {
      "lora_name": "flux/SydMead-v1.safetensors",
      "strength_model": 0.5,
      "strength_clip": 1,
      "model": [
        "27",
        0
      ],
      "clip": [
        "4",
        0
      ]
    },
    "class_type": "LoraLoader",
    "_meta": {
      "title": "Load LoRA (Model and CLIP)"
    }
  },
  "30": {
    "inputs": {
      "lora_name": "flux/SpaceshipGenerator-v2.safetensors",
      "strength_model": 0.3,
      "strength_clip": 1,
      "model": [
        "29",
        0
      ],
      "clip": [
        "29",
        1
      ]
    },
    "class_type": "LoraLoader",
    "_meta": {
      "title": "Load LoRA (Model and CLIP)"
    }
  }
}
"""

def queue_prompt(prompt):
	p = {"prompt": prompt}
	data = json.dumps(p).encode('utf-8')
	req =  request.Request(f"http://imagen:8188/prompt", data=data)
	request.urlopen(req)

def generate_image(description, entity_key):
	prompt = json.loads(prompt_text)
	#set the text prompt for our positive CLIPTextEncode
	prompt["43"]["inputs"]["text"] = description
	prompt["55"]["inputs"]["output_path"] = f"/media/imagens/{entity_key}"

	#set the seed for our KSampler node
	# prompt["3"]["inputs"]["seed"] = 5

	queue_prompt(prompt)

def generate_image(
		description,
		negative,
		entity_key,
		location_key=None,
		lora1="style/Anime art",
		lora1_weight=0.0,
		lora2="setting/ChineseWuXia",
		lora2_weight=0.0,
		width=1024,
		height=1024,
		steps=48
	):
	prompt = json.loads(prompt_text)
	prompt["3"]["inputs"]["steps"] = steps
	prompt["3"]["inputs"]["noise_seed"] = random.randint(0, 10000)
	prompt["24"]["inputs"]["width"] = width
	prompt["24"]["inputs"]["height"] = height
	prompt["25"]["inputs"]["text"] = description
	prompt["26"]["inputs"]["text"] = negative
	prompt["29"]["inputs"]["lora_name"] = f"flux/{ lora1 }.safetensors"
	prompt["29"]["inputs"]["strength_model"] = lora1_weight
	prompt["30"]["inputs"]["lora_name"] = f"flux/{ lora2 }.safetensors"
	prompt["30"]["inputs"]["strength_model"] = lora2_weight
	if location_key:
		prompt["28"]["inputs"]["output_path"] = f"/media/imagens/{entity_key}/{location_key}"
	else:
		prompt["28"]["inputs"]["output_path"] = f"/media/imagens/{entity_key}"
	
	queue_prompt(prompt)

	print(f"imagen:\nentity_key: { entity_key }\nlora1: { lora1 }:{ lora1_weight }\nlora2: { lora2 }:{ lora2_weight }\nwidth: { width }\nheight: { height }\n\t{ description }\n\t{ negative }")


# generate_image("a cow", "123456")
