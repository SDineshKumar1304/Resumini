import os
import yaml

def load_config(path="configs/config.yaml"):
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return yaml.safe_load(f)

def ensure_dir(path):
    import os
    os.makedirs(path, exist_ok=True)
