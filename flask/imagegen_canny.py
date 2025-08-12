import json
from urllib import request, parse
import random
import os


prompt_text = """
{
  "6": {
    "inputs": {
      "text": [
        "48",
        0
      ],
      "clip": [
        "39",
        1
      ]
    },
    "class_type": "CLIPTextEncode",
    "_meta": {
      "title": "CLIP Text Encode (Positive Prompt)"
    }
  },
  "8": {
    "inputs": {
      "samples": [
        "13",
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
      "vae_name": "flux/ae.safetensors",
      "+": null
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "13": {
    "inputs": {
      "noise": [
        "25",
        0
      ],
      "guider": [
        "22",
        0
      ],
      "sampler": [
        "16",
        0
      ],
      "sigmas": [
        "17",
        0
      ],
      "latent_image": [
        "27",
        0
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "16": {
    "inputs": {
      "sampler_name": "dpmpp_2m"
    },
    "class_type": "KSamplerSelect",
    "_meta": {
      "title": "KSamplerSelect"
    }
  },
  "17": {
    "inputs": {
      "scheduler": "beta",
      "steps": 24,
      "denoise": 1,
      "model": [
        "30",
        0
      ]
    },
    "class_type": "BasicScheduler",
    "_meta": {
      "title": "BasicScheduler"
    }
  },
  "22": {
    "inputs": {
      "model": [
        "30",
        0
      ],
      "conditioning": [
        "26",
        0
      ]
    },
    "class_type": "BasicGuider",
    "_meta": {
      "title": "BasicGuider"
    }
  },
  "25": {
    "inputs": {
      "noise_seed": 32
    },
    "class_type": "RandomNoise",
    "_meta": {
      "title": "RandomNoise"
    }
  },
  "26": {
    "inputs": {
      "guidance": 3.5,
      "conditioning": [
        "6",
        0
      ]
    },
    "class_type": "FluxGuidance",
    "_meta": {
      "title": "FluxGuidance"
    }
  },
  "27": {
    "inputs": {
      "width": [
        "49",
        0
      ],
      "height": [
        "49",
        1
      ],
      "batch_size": 1
    },
    "class_type": "EmptySD3LatentImage",
    "_meta": {
      "title": "EmptySD3LatentImage"
    }
  },
  "30": {
    "inputs": {
      "max_shift": 1.15,
      "base_shift": 0.5,
      "width": [
        "49",
        0
      ],
      "height": [
        "49",
        1
      ],
      "model": [
        "39",
        0
      ]
    },
    "class_type": "ModelSamplingFlux",
    "_meta": {
      "title": "ModelSamplingFlux"
    }
  },
  "39": {
    "inputs": {
      "model": [
        "55",
        0
      ],
      "clip": [
        "54",
        0
      ],
      "lora_stack": [
        "41",
        2
      ]
    },
    "class_type": "CR Apply LoRA Stack",
    "_meta": {
      "title": "💊 CR Apply LoRA Stack"
    }
  },
  "40": {
    "inputs": {
      "lora_name": "flux/style/OilPaintingD4n.safetensors",
      "lora_weight": 0.6000000000000001,
      "force_fetch": true,
      "append_loraname_if_empty": false
    },
    "class_type": "LoraLoaderStackedVanilla",
    "_meta": {
      "title": "LoraLoaderStackedVanilla"
    }
  },
  "41": {
    "inputs": {
      "lora_name": "flux/style/Anime art.safetensors",
      "lora_weight": 0.6000000000000001,
      "force_fetch": true,
      "append_loraname_if_empty": false,
      "lora_stack": [
        "40",
        2
      ]
    },
    "class_type": "LoraLoaderStackedVanilla",
    "_meta": {
      "title": "LoraLoaderStackedVanilla"
    }
  },
  "42": {
    "inputs": {
      "delimiter": ", ",
      "text_list": [
        "40",
        0
      ]
    },
    "class_type": "Text List to Text",
    "_meta": {
      "title": "Text List to Text"
    }
  },
  "43": {
    "inputs": {
      "delimiter": ", ",
      "text_list": [
        "41",
        0
      ]
    },
    "class_type": "Text List to Text",
    "_meta": {
      "title": "Text List to Text"
    }
  },
  "44": {
    "inputs": {
      "Text": "superhero, young man, short hair, black hair, costume, city"
    },
    "class_type": "DF_Text_Box",
    "_meta": {
      "title": "Text Box"
    }
  },
  "48": {
    "inputs": {
      "delimiter": ", ",
      "clean_whitespace": "true",
      "text_a": [
        "44",
        0
      ],
      "text_b": [
        "42",
        0
      ],
      "text_c": [
        "43",
        0
      ]
    },
    "class_type": "Text Concatenate",
    "_meta": {
      "title": "Text Concatenate"
    }
  },
  "49": {
    "inputs": {
      "width": 1024,
      "height": 1024,
      "aspect_ratio": "5:8 portrait 832x1216",
      "swap_dimensions": "Off",
      "upscale_factor": 1,
      "batch_size": 1
    },
    "class_type": "CR SDXL Aspect Ratio",
    "_meta": {
      "title": "🔳 CR SDXL Aspect Ratio"
    }
  },
  "50": {
    "inputs": {
      "value": 32,
      "mode": true,
      "action": "increment",
      "last_seed": 31
    },
    "class_type": "GlobalSeed //Inspire",
    "_meta": {
      "title": "Global Seed (Inspire)"
    }
  },
  "54": {
    "inputs": {
      "clip_name1": "flux/t5xxl_fp8_e4m3fn.safetensors",
      "clip_name2": "flux/clip_l.safetensors",
      "type": "flux"
    },
    "class_type": "DualCLIPLoaderGGUF",
    "_meta": {
      "title": "DualCLIPLoader (GGUF)"
    }
  },
  "55": {
    "inputs": {
      "unet_name": "fluxArtFusionV10FP16_v10FP16GGUFQ8.gguf"
    },
    "class_type": "UnetLoaderGGUF",
    "_meta": {
      "title": "Unet Loader (GGUF)"
    }
  },
  "57": {
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
	prompt["44"]["inputs"]["Text"] = description
	prompt["57"]["inputs"]["output_path"] = f"{os.environ['MEDIA_FOLDER']}/imagens/{entity_key}"

	#set the seed for our KSampler node
	# prompt["3"]["inputs"]["seed"] = 5

	queue_prompt(prompt)

def generate_image(description, entity_key, lora1="style/Anime art", lora1_weight=0.5, lora2="setting/ChineseWuXia", lora2_weight=0.5, width=1024, height=1024):
	prompt = json.loads(prompt_text)
	prompt["44"]["inputs"]["Text"] = description
	prompt["57"]["inputs"]["output_path"] = f"{os.environ['MEDIA_FOLDER']}/imagens/{entity_key}"
	prompt["40"]["inputs"]["lora_name"] = f"flux/{ lora1 }.safetensors"
	prompt["40"]["inputs"]["lora_weight"] = lora1_weight
	prompt["41"]["inputs"]["lora_name"] = f"flux/{ lora2 }.safetensors"
	prompt["41"]["inputs"]["lora_weight"] = lora2_weight
	prompt["25"]["inputs"]["noise_seed"] = random.randint(0, 10000)
	prompt["49"]["inputs"]["width"] = width
	prompt["49"]["inputs"]["height"] = height
	
	queue_prompt(prompt)


# generate_image("a cow", "123456")
