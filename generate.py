from diffusers import DiffusionPipeline
from diffusers.utils import pt_to_pil
import torch
import gc
import torch
import argparse

parser = argparse.ArgumentParser(
                    prog='IF_image_generator')
parser.add_argument('prompt')  
args = parser.parse_args()
prompt=args.prompt #"Abstract pencil and watercolor art of  Florian, a young boy with a golden donkey standing under a tree in a magical forest."


def flush():
  gc.collect()
  torch.cuda.empty_cache()


# stage 1
stage_1 = DiffusionPipeline.from_pretrained("DeepFloyd/IF-I-XL-v1.0", variant="fp16", torch_dtype=torch.float16)
#stage_1.enable_xformers_memory_efficient_attention()  # remove line if torch.__version__ >= 2.0.0
stage_1.enable_model_cpu_offload()

# stage 2
stage_2 = DiffusionPipeline.from_pretrained(
    "DeepFloyd/IF-II-L-v1.0", text_encoder=None, variant="fp16", torch_dtype=torch.float16
)
#stage_2.enable_xformers_memory_efficient_attention()  # remove line if torch.__version__ >= 2.0.0
stage_2.enable_model_cpu_offload()

# stage 3
#safety_modules = {"feature_extractor": stage_1.feature_extractor, "safety_checker": stage_1.safety_checker, "watermarker": stage_1.watermarker}
stage_3 = DiffusionPipeline.from_pretrained("stabilityai/stable-diffusion-x4-upscaler", torch_dtype=torch.float16)
#stage_3.enable_xformers_memory_efficient_attention()  # remove line if torch.__version__ >= 2.0.0
stage_3.enable_model_cpu_offload()

#prompt = 'a photo of a kangaroo wearing an orange hoodie and blue sunglasses standing in front of the eiffel tower holding a sign that says "very deep learning"'

# text embeds
prompt_embeds, negative_embeds = stage_1.encode_prompt(prompt)

generator = torch.manual_seed(0)

# stage 1
image = stage_1(prompt_embeds=prompt_embeds, negative_prompt_embeds=negative_embeds, generator=generator, output_type="pt").images
del stage_1
flush()
pt_to_pil(image)[0].save("./if_stage_I.png")

# stage 2
image = stage_2(
    image=image, prompt_embeds=prompt_embeds, negative_prompt_embeds=negative_embeds, generator=generator, output_type="pt"
).images

del stage_2
flush()

pt_to_pil(image)[0].save("./if_stage_II.png")

print("running stage 3")
# stage 3
image = stage_3(prompt=prompt, image=image, generator=generator, noise_level=100).images
print("saving")
image[0].save("./if_stage_III.png")

