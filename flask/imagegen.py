import json
from urllib import request
import random
import os


prompt_text = """
{
  "4": {
    "inputs": {
      "noise_seed": 365437518561265,
      "steps": 28,
      "timestep_to_start_cfg": 1,
      "true_gs": 3.5,
      "image_to_image_strength": 0,
      "denoise_strength": 1,
      "model": [
        "18",
        0
      ],
      "conditioning": [
        "44",
        0
      ],
      "neg_conditioning": [
        "45",
        0
      ],
      "latent_image": [
        "16",
        4
      ]
    },
    "class_type": "XlabsSampler",
    "_meta": {
      "title": "Xlabs Sampler"
    }
  },
  "9": {
    "inputs": {
      "clip_name1": "flux/t5xxl_fp8_e4m3fn.safetensors",
      "clip_name2": "flux/clip_l.safetensors",
      "type": "flux",
      "device": "default",
      "+": null
    },
    "class_type": "DualCLIPLoader",
    "_meta": {
      "title": "DualCLIPLoader"
    }
  },
  "11": {
    "inputs": {
      "samples": [
        "4",
        0
      ],
      "vae": [
        "13",
        0
      ]
    },
    "class_type": "VAEDecode",
    "_meta": {
      "title": "VAE Decode"
    }
  },
  "13": {
    "inputs": {
      "vae_name": "flux/ae.safetensors",
      "+": null
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "16": {
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
  "18": {
    "inputs": {
      "model": [
        "47",
        0
      ],
      "clip": [
        "26",
        0
      ],
      "lora_stack": [
        "24",
        2
      ]
    },
    "class_type": "CR Apply LoRA Stack",
    "_meta": {
      "title": "💊 CR Apply LoRA Stack"
    }
  },
  "24": {
    "inputs": {
      "lora_name": "flux/setting/Hyperborea-v2.safetensors",
      "lora_weight": 0.4000000000000001,
      "force_fetch": true,
      "append_loraname_if_empty": false,
      "lora_stack": [
        "25",
        2
      ]
    },
    "class_type": "LoraLoaderStackedVanilla",
    "_meta": {
      "title": "LoraLoaderStackedVanilla"
    }
  },
  "25": {
    "inputs": {
      "lora_name": "flux/import/XuErGuangying.safetensors",
      "lora_weight": 0.8000000000000002,
      "force_fetch": true,
      "append_loraname_if_empty": false
    },
    "class_type": "LoraLoaderStackedVanilla",
    "_meta": {
      "title": "LoraLoaderStackedVanilla"
    }
  },
  "26": {
    "inputs": {
      "stop_at_clip_layer": -2,
      "clip": [
        "9",
        0
      ]
    },
    "class_type": "CLIPSetLastLayer",
    "_meta": {
      "title": "CLIP Set Last Layer"
    }
  },
  "44": {
    "inputs": {
      "clip_l": [
        "53",
        0
      ],
      "t5xxl": [
        "53",
        0
      ],
      "guidance": 4.0,
      "speak_and_recognation": {
        "__value__": [
          false,
          true
        ]
      },
      "clip": [
        "18",
        1
      ]
    },
    "class_type": "CLIPTextEncodeFlux",
    "_meta": {
      "title": "CLIPTextEncodeFlux"
    }
  },
  "45": {
    "inputs": {
      "clip_l": "bad or low quality",
      "t5xxl": "bad or low quality",
      "guidance": 4.0,
      "speak_and_recognation": {
        "__value__": [
          false,
          true
        ]
      },
      "clip": [
        "18",
        1
      ]
    },
    "class_type": "CLIPTextEncodeFlux",
    "_meta": {
      "title": "CLIPTextEncodeFlux"
    }
  },
  "46": {
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
        "11",
        0
      ]
    },
    "class_type": "Image Save",
    "_meta": {
      "title": "Image Save"
    }
  },
  "47": {
    "inputs": {
      "unet_name": "fluxArtFusionV10FP16_v10FP16GGUFQ8.gguf"
    },
    "class_type": "UnetLoaderGGUF",
    "_meta": {
      "title": "Unet Loader (GGUF)"
    }
  },
  "48": {
    "inputs": {
      "delimiter": ", ",
      "text_list": [
        "24",
        0
      ]
    },
    "class_type": "Text List to Text",
    "_meta": {
      "title": "Text List to Text"
    }
  },
  "50": {
    "inputs": {
      "delimiter": ", ",
      "text_list": [
        "25",
        0
      ]
    },
    "class_type": "Text List to Text",
    "_meta": {
      "title": "Text List to Text"
    }
  },
  "53": {
    "inputs": {
      "delimiter": ", ",
      "clean_whitespace": "true",
      "text_a": [
        "54",
        0
      ],
      "text_b": [
        "50",
        0
      ],
      "text_c": [
        "48",
        0
      ]
    },
    "class_type": "Text Concatenate",
    "_meta": {
      "title": "Text Concatenate"
    }
  },
  "54": {
    "inputs": {
      "text": "",
      "speak_and_recognation": {
        "__value__": [
          false,
          true
        ]
      }
    },
    "class_type": "Text Multiline",
    "_meta": {
      "title": "Text Multiline"
    }
  },
  "56": {
    "inputs": {
      "text": [
        "53",
        0
      ],
      "label": "positive image prompt"
    },
    "class_type": "Text to Console",
    "_meta": {
      "title": "Text to Console"
    }
  }
}
"""

def queue_prompt(prompt):
	p = {"prompt": prompt}
	data = json.dumps(p).encode('utf-8')
	req =  request.Request(f"http://{os.environ['PUBLIC_IP']}:8188/prompt", data=data)
	request.urlopen(req)

def generate_image(description, entity_key):
	prompt = json.loads(prompt_text)
	#set the text prompt for our positive CLIPTextEncode
	prompt["54"]["inputs"]["text"] = description
	prompt["46"]["inputs"]["output_path"] = f"{os.environ['MEDIA_FOLDER']}/imagens/{entity_key}"

	#set the seed for our KSampler node
	# prompt["3"]["inputs"]["seed"] = 5

	queue_prompt(prompt)

def generate_image(
		description,
		negative,
		entity_key,
		location_key=None,
		lora1="style/Anime art",
		lora1_weight=0.5,
		lora2="setting/ChineseWuXia",
		lora2_weight=0.5,
		width=1024,
		height=1024
	):
	prompt = json.loads(prompt_text)
	prompt["16"]["inputs"]["width"] = width
	prompt["16"]["inputs"]["height"] = height
	prompt["54"]["inputs"]["text"] = description
	prompt["45"]["inputs"]["clip_l"] = negative
	prompt["45"]["inputs"]["t5xxl"] = negative
	prompt["24"]["inputs"]["lora_name"] = f"flux/{ lora1 }.safetensors"
	prompt["24"]["inputs"]["lora_weight"] = lora1_weight
	prompt["25"]["inputs"]["lora_name"] = f"flux/{ lora2 }.safetensors"
	prompt["25"]["inputs"]["lora_weight"] = lora2_weight
	prompt["4"]["inputs"]["noise_seed"] = random.randint(0, 10000)
	if location_key:
		prompt["46"]["inputs"]["output_path"] = f"{os.environ['MEDIA_FOLDER']}/imagens/{entity_key}/{location_key}"
	else:
		prompt["46"]["inputs"]["output_path"] = f"{os.environ['MEDIA_FOLDER']}/imagens/{entity_key}"
	
	print(f"imagen:\nentity_key: { entity_key }\nlora1: { lora1 }:{ lora1_weight }\nlora2: { lora2 }:{ lora2_weight }\nwidth: { width }\nheight: { height }\n\t{ description }\n\t{ negative }")

	queue_prompt(prompt)


# generate_image("a cow", "123456")
