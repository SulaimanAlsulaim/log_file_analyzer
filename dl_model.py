# dl_model.py (Ultra Optimized for RTX 2060 SUPER)

import time
import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# ==============================
# CONFIG
# ==============================
MODEL_DIR = "ILFA_Deployment/best_model_balanced"
THRESHOLD = 0.8

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

print("🔧 Initializing Deep Learning Model...")
print(f"   ➤ Detected device: {DEVICE}")

# ==============================
# LOAD TOKENIZER & MODEL
# ==============================
tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)

if DEVICE == "cuda":
    print("   ➤ Loading model in FP16 (GPU accelerated)...")
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_DIR,
        torch_dtype=torch.float16
    )
else:
    print("   ➤ Loading model in FP32 (CPU mode)...")
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)

model.to(DEVICE)
model.eval()

print("✅ DL Model Loaded and Ready!\n")


# ==============================
# MAIN INFERENCE FUNCTION
# ==============================
def run_dl_on_parsed(df: pd.DataFrame, batch_size: int = 512) -> pd.DataFrame:
    """
    Runs anomaly detection on a structured log DataFrame.
    GPU optimized for RTX 2060 SUPER.
    """

    if "Content" not in df.columns:
        raise ValueError("Structured DF must contain 'Content' column.")

    texts = df["Content"].astype(str).tolist()
    n = len(texts)

    print(f"🧠 Running Deep Learning Model on {n} lines (device={DEVICE})...")
    t_start = time.time()

    scores = []

    num_batches = max(1, (n + batch_size - 1) // batch_size)

    for b in range(num_batches):
        start = b * batch_size
        end = min(start + batch_size, n)
        batch_texts = texts[start:end]

        print(f"   ➤ Batch {b + 1}/{num_batches}  ({start}–{end - 1})")

        # Tokenize
        encodings = tokenizer(
            batch_texts,
            padding=True,
            truncation=True,
            max_length=256,
            return_tensors="pt"
        )

        # Fast transfer to GPU
        encodings = {k: v.to(DEVICE, non_blocking=True) for k, v in encodings.items()}

        # GPU optimized inference
        with torch.inference_mode():
            logits = model(**encodings).logits

            # 🔥 Softmax on GPU (faster)
            probs = torch.softmax(logits, dim=-1)[:, 1]

            # Move ONLY the final vector to CPU
            probs = probs.float().cpu().numpy()

        scores.extend(probs)

    # Attach results
    df["anomaly_score"] = scores
    df["pred_label"] = (df["anomaly_score"] >= THRESHOLD).astype(int)

    t_total = time.time() - t_start
    print(f"✅ DL Inference Completed in {t_total:.2f} seconds.\n")

    return df
