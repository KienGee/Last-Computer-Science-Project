"""
Script để upload model lên HuggingFace Hub
"""
from huggingface_hub import HfApi, create_repo
import os

# Cấu hình
MODEL_PATH = "models/final_vit5_model_phase2"
REPO_ID = "NishiKyen/vit5-vietnamese-news"

# Khởi tạo API
api = HfApi()

print(f"🚀 Uploading model to {REPO_ID}...")

try:
    # Tạo repo nếu chưa có (repo đã tồn tại rồi nên có thể skip)
    print("📝 Creating/verifying repository...")
    create_repo(REPO_ID, repo_type="model", exist_ok=True)
    
    # Upload từng file
    files_to_upload = [
        "config.json",
        "generation_config.json", 
        "model.safetensors",
        "special_tokens_map.json",
        "spiece.model",
        "tokenizer_config.json"
    ]
    
    for filename in files_to_upload:
        file_path = os.path.join(MODEL_PATH, filename)
        if os.path.exists(file_path):
            print(f"⬆️  Uploading {filename}...")
            api.upload_file(
                path_or_fileobj=file_path,
                path_in_repo=filename,
                repo_id=REPO_ID,
                repo_type="model"
            )
            print(f"✅ {filename} uploaded successfully")
        else:
            print(f"⚠️  {filename} not found, skipping...")
    
    print(f"\n✅ Model uploaded successfully!")
    print(f"🔗 View at: https://huggingface.co/{REPO_ID}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nTry manual upload at: https://huggingface.co/NishiKyen/vit5-vietnamese-news/tree/main")
