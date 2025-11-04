import google.generativeai as genai
import os, yaml
import sys
import time

class GeminiLLM:
    def __init__(self):
        """
        Initialize the Gemini LLM using API key from configs/config.yaml
        """
        print("⚙️  Initializing agent...")
        try:
            config_path = os.path.join("configs", "config.yaml")
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"Missing config file: {config_path}")

            with open(config_path, "r") as f:
                cfg = yaml.safe_load(f)

            if "GEMINI_API_KEY" not in cfg:
                raise KeyError("GEMINI_API_KEY not found in config.yaml")

            genai.configure(api_key=cfg["GEMINI_API_KEY"])
            self.model = genai.GenerativeModel("gemini-2.5-flash"
                                            #    tools=[]
                                               )

            print("✅ Agent Initialized successfully!")

        except Exception as e:
            # print(f"❌ LLM initialization failed: {e}")
            sys.exit(1)

    def generate(self, prompt: str, max_tokens: int = None) -> str:
        """
        Generate text from the LLM with live streaming effect.
        """
        try:
            gen_cfg = {"max_output_tokens": max_tokens} if max_tokens else {}

            # Enable streaming from Gemini
            stream = self.model.generate_content(
                prompt,
                stream=True,
                generation_config=gen_cfg if gen_cfg else None
            )

            full_text = ""
            print("💬 Generating response...\n")

            for chunk in stream:
                if chunk.text:
                    for ch in chunk.text:
                        print(ch, end="", flush=True)
                        time.sleep(0.01)
                        full_text += ch
            print()  
            return ""
        except Exception as e:
            print(f"\n⚠️ LLM call failed: {e}")
            return "LLM not available. Please check API key or network."

    def stream(self, prompt: str, max_tokens: int = None):
        """
        Alias for generate(), to support .stream() calls from core.py.
        """
        return self.generate(prompt, max_tokens)
