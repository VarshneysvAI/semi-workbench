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
print("Starting request to deepseek without thinking...")
completion = client.chat.completions.create(
  model="deepseek-ai/deepseek-v4-flash-0731",
  messages=[{"role":"user","content":"Write a limerick about the wonders of GPU computing."}],
  temperature=0,
  max_tokens=1000,
  stream=False
)

print(f"Took {time.time() - start:.2f}s")
print("Content:", completion.choices[0].message.content)
