import google.generativeai as genai
import os

# Paste your API key here directly for the test
api_key = "AIzaSyACRERSsRceJfrNeKz0LmjiroKvkZ5iiZw"
genai.configure(api_key=api_key)

print("Listing available models...")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)