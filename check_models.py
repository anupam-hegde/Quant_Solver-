import google.generativeai as genai

# PASTE YOUR KEY HERE
genai.configure(api_key="")

print("Searching for available models...")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f"- {m.name}")
