"""
@author: shinich39
@title: Model DB
@nickname: Model DB
@version: 1.0.1
@description: Store settings by model.
"""

from server import PromptServer
from aiohttp import web
import torch

import os
import json
import comfy
import folder_paths
import folder_paths as comfy_paths

import latent_preview

DEBUG = False
VERSION = "1.0.1"
WEB_DIRECTORY = "./js"
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]

__DIRNAME = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(__DIRNAME, "db.json")
MAX_RESOLUTION = 16384

def chk_db():
  if os.path.exists(DB_PATH) == False:
    with open(DB_PATH, "w") as file:
      json.dump({}, file)

@PromptServer.instance.routes.get("/shinich39/model-db/get-models")
async def get_models(request):
  model_names = comfy_paths.get_filename_list("checkpoints")
  return web.json_response(model_names)

@PromptServer.instance.routes.get("/shinich39/model-db/get-default-values")
async def get_default_values(request):

  values = {
    # "ckpt_name": comfy_paths.get_filename_list("checkpoints")[0],
    "positive": "",
    "negative": "",
    "seed": 0,
    "control_after_generate": "randomize",
    "steps": 20,
    "cfg": 8.0,
    "sampler_name": comfy.samplers.KSampler.SAMPLERS[0],
    "scheduler": comfy.samplers.KSampler.SCHEDULERS[0],
    "denoise": 1.0,
    "width": 512,
    "height": 512,
  }
  
  return web.json_response(values)
  
@PromptServer.instance.routes.get("/shinich39/model-db/get-data")
async def get_db(request):

  chk_db()
  
  with open(DB_PATH, "r") as file:
    json_data = json.load(file)
    return web.json_response(json_data)

@PromptServer.instance.routes.post("/shinich39/model-db/set-data")
async def set_db(request):
  req = await request.json()
  ckpt = req["ckpt"]
  key = req["key"]
  values = req["values"]

  chk_db()

  with open(DB_PATH, "r") as file:
    json_data = json.load(file)

  if not ckpt in json_data:
    json_data[ckpt] = {}

  json_data[ckpt][key] = values

  with open(DB_PATH, "w") as file:
    json.dump(json_data, file, indent=2)

  return web.json_response(json_data)


@PromptServer.instance.routes.post("/shinich39/model-db/remove-data")
async def remove_db(request):
  req = await request.json()
  ckpt = req["ckpt"]
  key = req["key"]

  chk_db()

  with open(DB_PATH, "r") as file:
    json_data = json.load(file)

  if ckpt in json_data and key in json_data[ckpt]:
    del json_data[ckpt][key]

  with open(DB_PATH, "w") as file:
    json.dump(json_data, file)

  return web.json_response(json_data)

def load_ckpt(ckpt_name):
  if ckpt_name:
    ckpt_path = folder_paths.get_full_path("checkpoints", ckpt_name)
    ckpt = comfy.sd.load_checkpoint_guess_config(ckpt_path, output_vae=True, output_clip=True, embedding_directory=folder_paths.get_folder_paths("embeddings"))
    return (ckpt[0], ckpt[1], ckpt[2])
  else:
    return (None, None, None)

# /ComfuUI/nodes.py EmptyLatentImage
def generate_empty_latent_image(device, width, height, batch_size = 1):
  latent = torch.zeros([batch_size, 4, height // 8, width // 8], device=device)
  return {"samples":latent}

# /ComfuUI/nodes.py
def common_ksampler(model, seed, steps, cfg, sampler_name, scheduler, positive, negative, latent, denoise=1.0, disable_noise=False, start_step=None, last_step=None, force_full_denoise=False):
    latent_image = latent["samples"]
    if disable_noise:
        noise = torch.zeros(latent_image.size(), dtype=latent_image.dtype, layout=latent_image.layout, device="cpu")
    else:
        batch_inds = latent["batch_index"] if "batch_index" in latent else None
        noise = comfy.sample.prepare_noise(latent_image, seed, batch_inds)

    noise_mask = None
    if "noise_mask" in latent:
        noise_mask = latent["noise_mask"]

    callback = latent_preview.prepare_callback(model, steps)
    disable_pbar = not comfy.utils.PROGRESS_BAR_ENABLED
    samples = comfy.sample.sample(model, noise, steps, cfg, sampler_name, scheduler, positive, negative, latent_image,
                                  denoise=denoise, disable_noise=disable_noise, start_step=start_step, last_step=last_step,
                                  force_full_denoise=force_full_denoise, noise_mask=noise_mask, callback=callback, disable_pbar=disable_pbar, seed=seed)
    out = latent.copy()
    out["samples"] = samples
    return out

# /ComfuUI/nodes.py CLIPTextEncode
def encode_text(clip, text):
  tokens = clip.tokenize(text)
  cond, pooled = clip.encode_from_tokens(tokens, return_pooled=True)
  return [[cond, {"pooled_output": pooled}]]

# main  
class ModelDB():
  def __init__(self):
    self.device = comfy.model_management.intermediate_device()
    pass

  @classmethod
  def INPUT_TYPES(cls):
    return {
      "required": {
        "ckpt_name": (comfy_paths.get_filename_list("checkpoints"), ),
      },
      "optional": {
        "key": ([None], {"default": "", }),
        "positive": ("STRING", {"default": "", "multiline": True}),
        "negative": ("STRING", {"default": "", "multiline": True}),
        "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
        "steps": ("INT", {"default": 20, "min": 1, "max": 10000}),
        "cfg": ("FLOAT", {"default": 8.0, "min": 0.0, "max": 100.0}),
        "sampler_name": (comfy.samplers.KSampler.SAMPLERS, ),
        "scheduler": (comfy.samplers.KSampler.SCHEDULERS, ),
        "denoise": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
        "width": ("INT", {"default": 512, "min": 0, "max": MAX_RESOLUTION, "step": 8}),
        "height": ("INT", {"default": 512, "min": 0, "max": MAX_RESOLUTION, "step": 8}),
      },
    }
  
  FUNCTION = "exec"
  RETURN_TYPES = ("MODEL", "CLIP", "VAE", "STRING", "STRING", "INT", "INT", "FLOAT", "STRING", "STRING", "FLOAT", "INT", "INT", "LATENT",)
  RETURN_NAMES = ("MODEL", "CLIP", "VAE", "POSITIVE", "NEGATIVE", "SEED", "STEPS", "CFG", "SAMPLER_NAME", "SCHEDULER", "DENOISE", "WIDTH", "HEIGHT", "LATENT",)

  CATEGORY = "utils"

  def exec(self, ckpt_name, key, positive, negative, seed, steps, cfg, sampler_name, scheduler, denoise, width, height):
    if DEBUG:
      print(f"ckpt_name: {ckpt_name}")
      print(f"key: {key}")
      print(f"positive: {positive}")
      print(f"negative: {negative}")
      print(f"seed: {seed}")
      print(f"steps: {steps}")
      print(f"cfg: {cfg}")
      print(f"sampler_name: {sampler_name}")
      print(f"scheduler: {scheduler}")
      print(f"denoise: {denoise}")
      print(f"width: {width}")
      print(f"height: {height}")

    model, clip, vae = load_ckpt(ckpt_name)

    if DEBUG:
      print(f"model: {model}")
      print(f"clip: {clip}")
      print(f"vae: {vae}")

    encoded_positive = encode_text(clip, positive)
    encoded_negative = encode_text(clip, negative)

    if DEBUG:
      print(f"encoded_positive: {encoded_positive}")
      print(f"encoded_negative: {encoded_negative}")
    
    latent_image = generate_empty_latent_image(self.device, width, height)

    if DEBUG:
      print(f"latent_image: {latent_image}")

    latent = common_ksampler(model, seed, steps, cfg, sampler_name, scheduler, encoded_positive, encoded_negative, latent_image, denoise=denoise)

    if DEBUG:
      print(f"latent: {latent}")

    return (model, clip, vae, positive, negative, seed, steps, cfg, sampler_name, scheduler, denoise, width, height, latent)

NODE_CLASS_MAPPINGS["Model DB"] = ModelDB
NODE_DISPLAY_NAME_MAPPINGS["Model DB"] = "Model DB"