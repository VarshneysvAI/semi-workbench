import os
import time
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv('backend/.env')

client = OpenAI(
  base_url = "https://integrate.api.nvidia.com/v1",
  api_key = os.getenv("NIM_API_KEY") or os.getenv("LLM_API_KEY_NIM")
)

start = time.time()
print("Starting request to nemotron-3.5-lightning-30b-a3b...")
completion = client.chat.completions.create(
  model="nvidia/nemotron-3.5-lightning-30b-a3b",
  messages=[{"role":"user","content":"Write a limerick about the wonders of GPU computing."}],
  temperature=1,
  top_p=0.95,
  max_tokens=1000,
  extra_body={"chat_template_kwargs":{"enable_thinking":True},"reasoning_budget":1000},
  stream=False
)

print(f"Took {time.time() - start:.2f}s")
message = completion.choices[0].message
reasoning = getattr(message, "reasoning_content", None)
if reasoning:
  print("Reasoning:", reasoning[:200])
print("Content:", message.content)
