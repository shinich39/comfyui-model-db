# comfyui-model-db

Store settings by model.

![image-1](./images/workflow.png)

## Usage

Add node > utils > Model DB

Save settings with current checkpoint and current time key as ID.

You can't change key name for simplify process flow.

## Output types

| Field        | Type  | Info                                      |
|--------------|-------|-------------------------------------------|
| MODEL        | MODEL |                                           |
| CLIP         | CLIP  |                                           |
| VAE          | VAE   |                                           |
| POSITIVE     | TEXT  |                                           |
| NEGATIVE     | TEXT  |                                           |
| SEED         | INT   |                                           |
| CFG          | FLOAT |                                           |
| SAMPLER_NAME | TEXT  | Can not link KSampler sampler_name input. |
| SCHEDULER    | TEXT  | Can not link KSampler scheduler input.    |
| DENOISE      | FLOAT |                                           |
| WIDTH        | INT   |                                           |
| HEIGHT       | INT   |                                           |
| LATENT       | LATENT|                                           |

## Updates

- Add output latent
- Change widget positions