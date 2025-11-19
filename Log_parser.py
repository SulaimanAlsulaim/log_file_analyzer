import os
import json
import io
import time
import pandas as pd
from drain3 import TemplateMiner
from drain3.template_miner_config import TemplateMinerConfig
from drain3.file_persistence import FilePersistence

# Import DL model only once
from dl_model import run_dl_on_parsed


# ==========================================
# 🔧 Drain3 Setup
# ==========================================
STATE_FILE = "drain3_state.bin"


def build_template_miner(state_path=STATE_FILE):
    """Create and configure a TemplateMiner instance."""
    cfg = TemplateMinerConfig()
    cfg.profiling_enabled = False
    cfg.drain_sim_th = 0.4
    cfg.drain_depth = 4
    cfg.drain_max_children = 100
    cfg.drain_max_clusters = 20000
    cfg.drain_extra_delimiters = ";,()"
    cfg.drain_param_str = "<*>"

    folder = os.path.dirname(state_path)
    if folder and not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)

    persistence = FilePersistence(state_path)
    return TemplateMiner(persistence, cfg)


def parse_log_lines(lines):
    """Parse list of logs using Drain3."""
    tm = build_template_miner()
    rows = []

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        result = tm.add_log_message(line)

        rows.append({
            "LineId": i,
            "Content": line,
            "EventId": result["cluster_id"],
            "EventTemplate": result["template_mined"]
        })

    return pd.DataFrame(rows)


# ==========================================
# 🔥 MAIN FUNCTION
# ==========================================
def parse_uploaded_file(content: str, ext: str):
    """
    Accepts CSV, JSON, LOG, TXT
    Parses with Drain3
    Runs DL anomaly detection
    """

    print("\n==============================")
    print("📥 Starting Upload Process...")
    print("==============================")

    t_start = time.time()

    # ==========================================
    # STEP 1 ─ Extract raw lines
    # ==========================================
    print(f"📄 Reading uploaded file ({ext})...")

    t1 = time.time()

    # --- CSV ---
    if ext == "csv":
        try:
            df = pd.read_csv(io.StringIO(content), sep=None, engine="python")
            if "message" in df.columns:
                log_lines = df["message"].astype(str).tolist()
            else:
                log_lines = df.iloc[:, 0].astype(str).tolist()
        except Exception:
            log_lines = [line for line in content.splitlines()]

    # --- JSON ---
    elif ext == "json":
        try:
            df = pd.read_json(io.StringIO(content))
            if "message" in df.columns:
                log_lines = df["message"].astype(str).tolist()
            else:
                log_lines = df.iloc[:, 0].astype(str).tolist()
        except Exception:
            log_lines = [str(x) for x in json.loads(content)]

    # --- LOG / TXT ---
    elif ext in {"log", "txt"}:
        log_lines = content.splitlines()

    else:
        raise ValueError("Unsupported file extension")

    print(f"✔ Step 1 Done in {time.time() - t1:.2f} seconds")
    print(f"📌 Extracted {len(log_lines)} lines")

    # ==========================================
    # STEP 2 ─ Drain3 Parsing
    # ==========================================
    print("🔍 Parsing (Drain3)...")
    t2 = time.time()

    parsed_df = parse_log_lines(log_lines)

    print(f"✔ Step 2 Done in {time.time() - t2:.2f} seconds")
    print(f"📌 Parsed {len(parsed_df)} structured lines")

    # ==========================================
    # STEP 3 ─ Deep Learning Inference
    # ==========================================
    print("🧠 Running Deep Learning Model...")
    t3 = time.time()

    parsed_df = run_dl_on_parsed(parsed_df)

    print(f"✔ Step 3 Done in {time.time() - t3:.2f} seconds")

    # ==========================================
    # DONE
    # ==========================================
    print(f"🎉 Parsing process completed! Total time: {time.time() - t_start:.2f}s\n")

    return parsed_df
