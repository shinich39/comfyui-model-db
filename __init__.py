"""
@author: shinich39
@title: Model DB
@nickname: Model DB
@version: 1.0.0
@description: Store settings by model.
"""

from server import PromptServer
from aiohttp import web
import os
import json
import comfy
import folder_paths
import folder_paths as comfy_paths

DEBUG = False
VERSION = "1.0.0"
WEB_DIRECTORY = "./js"
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]

__DIRNAME = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(__DIRNAME, "db.json")
MAX_RESOLUTION=16384

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

# main  
class ModelDB():
  def __init__(self):
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
  RETURN_TYPES = ("MODEL", "CLIP", "VAE", "STRING", "STRING", "INT", "INT", "FLOAT", "STRING", "STRING", "FLOAT", "INT", "INT",)
  RETURN_NAMES = ("model", "clip", "vae", "positive", "negative", "seed", "steps", "cfg", "sampler_name", "scheduler", "denoise", "width", "height",)

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

    # load ckpt
    if ckpt_name:
      ckpt_path = folder_paths.get_full_path("checkpoints", ckpt_name)
      ckpt = comfy.sd.load_checkpoint_guess_config(ckpt_path, output_vae=True, output_clip=True, embedding_directory=folder_paths.get_folder_paths("embeddings"))
    else:
      ckpt = [None, None, None]
    
    return (ckpt[0], ckpt[1], ckpt[2], positive, negative, seed, steps, cfg, sampler_name, scheduler, denoise, width, height)

NODE_CLASS_MAPPINGS["Model DB"] = ModelDB
NODE_DISPLAY_NAME_MAPPINGS["Model DB"] = "Model DB"