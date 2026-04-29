import json
from urllib import request
import random
import os


prompt_text = """
{
  "8": {
    "inputs": {
      "samples": [
        "40",
        0
      ],
      "vae": [
        "10",
        0
      ]
    },
    "class_type": "VAEDecode",
    "_meta": {
      "title": "VAE Decode"
    }
  },
  "10": {
    "inputs": {
      "vae_name": "flux/ae.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "11": {
    "inputs": {
      "clip_name1": "flux/flan_t5_xxl_full_FP8e4m3.safetensors",
      "clip_name2": "flux/Long-ViT-L-14-BEST-GmP-smooth-ft.safetensors",
      "type": "flux",
      "device": "default"
    },
    "class_type": "DualCLIPLoader",
    "_meta": {
      "title": "DualCLIPLoader"
    }
  },
  "17": {
    "inputs": {
      "scheduler": "normal",
      "steps": 24,
      "denoise": 1,
      "model": [
        "50",
        0
      ]
    },
    "class_type": "BasicScheduler",
    "_meta": {
      "title": "BasicScheduler"
    }
  },
  "40": {
    "inputs": {
      "noise": [
        "45",
        0
      ],
      "guider": [
        "56",
        0
      ],
      "sampler": [
        "47",
        0
      ],
      "sigmas": [
        "17",
        0
      ],
      "latent_image": [
        "44",
        0
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "42": {
    "inputs": {
      "guidance": 4.0,
      "conditioning": [
        "43",
        0
      ]
    },
    "class_type": "FluxGuidance",
    "_meta": {
      "title": "FluxGuidance"
    }
  },
  "43": {
    "inputs": {
      "text": "powerful xianxia practitioner in midair on a horizontal chinese sword (like a skateboard:0.4)",
      "clip": [
        "11",
        0
      ]
    },
    "class_type": "CLIPTextEncode",
    "_meta": {
      "title": "CLIP Text Encode (Prompt)"
    }
  },
  "44": {
    "inputs": {
      "width": [
        "51",
        0
      ],
      "height": [
        "51",
        1
      ],
      "batch_size": 1
    },
    "class_type": "EmptySD3LatentImage",
    "_meta": {
      "title": "EmptySD3LatentImage"
    }
  },
  "45": {
    "inputs": {
      "noise_seed": 765637178901317
    },
    "class_type": "RandomNoise",
    "_meta": {
      "title": "RandomNoise"
    }
  },
  "47": {
    "inputs": {
      "sampler_name": "euler"
    },
    "class_type": "KSamplerSelect",
    "_meta": {
      "title": "KSamplerSelect"
    }
  },
  "48": {
    "inputs": {
      "unet_name": "flux/KreaDevFP8_fp16.safetensors",
      "weight_dtype": "default"
    },
    "class_type": "UNETLoader",
    "_meta": {
      "title": "Load Diffusion Model"
    }
  },
  "50": {
    "inputs": {
      "lora_name": "flux/OrientalFantasyIllustration.safetensors",
      "strength_model": 0.2,
      "model": [
        "52",
        0
      ]
    },
    "class_type": "LoraLoaderModelOnly",
    "_meta": {
      "title": "Load LoRA"
    }
  },
  "51": {
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
  "52": {
    "inputs": {
      "lora_name": "flux/CultivationNovel.safetensors",
      "strength_model": 0.4,
      "model": [
        "48",
        0
      ]
    },
    "class_type": "LoraLoaderModelOnly",
    "_meta": {
      "title": "Load LoRA"
    }
  },
  "55": {
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
        "8",
        0
      ]
    },
    "class_type": "Image Save",
    "_meta": {
      "title": "Image Save"
    }
  },
  "56": {
    "inputs": {
      "cfg": 1,
      "neg_scale": 4.0,
      "model": [
        "50",
        0
      ],
      "positive": [
        "42",
        0
      ],
      "negative": [
        "57",
        0
      ],
      "empty_conditioning": [
        "58",
        0
      ]
    },
    "class_type": "PerpNegGuider",
    "_meta": {
      "title": "PerpNegGuider"
    }
  },
  "57": {
    "inputs": {
      "text": "male",
      "clip": [
        "11",
        0
      ]
    },
    "class_type": "CLIPTextEncode",
    "_meta": {
      "title": "CLIP Text Encode (Prompt)"
    }
  },
  "58": {
    "inputs": {
      "text": "",
      "clip": [
        "11",
        0
      ]
    },
    "class_type": "CLIPTextEncode",
    "_meta": {
      "title": "CLIP Text Encode (Prompt)"
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
	prompt["17"]["inputs"]["steps"] = steps
	prompt["51"]["inputs"]["width"] = width
	prompt["51"]["inputs"]["height"] = height
	prompt["43"]["inputs"]["text"] = description
	prompt["57"]["inputs"]["text"] = negative
	prompt["52"]["inputs"]["lora_name"] = f"flux/{ lora1 }.safetensors"
	prompt["52"]["inputs"]["strength_model"] = lora1_weight
	prompt["50"]["inputs"]["lora_name"] = f"flux/{ lora2 }.safetensors"
	prompt["50"]["inputs"]["strength_model"] = lora2_weight
	prompt["45"]["inputs"]["noise_seed"] = random.randint(0, 10000)
	if location_key:
		prompt["55"]["inputs"]["output_path"] = f"/media/imagens/{entity_key}/{location_key}"
	else:
		prompt["55"]["inputs"]["output_path"] = f"/media/imagens/{entity_key}"
	
	queue_prompt(prompt)

	print(f"imagen:\nentity_key: { entity_key }\nlora1: { lora1 }:{ lora1_weight }\nlora2: { lora2 }:{ lora2_weight }\nwidth: { width }\nheight: { height }\n\t{ description }\n\t{ negative }")


# generate_image("a cow", "123456")
