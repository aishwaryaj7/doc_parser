import os
from pathlib import Path

CWD = Path().cwd()
DATA_DIR = CWD.joinpath("data")

OUTPUT_TEXT_DIR = DATA_DIR / "extracted_text"
OUTPUT_IMG_DIR = DATA_DIR / "extracted_images"
OUTPUT_TABLE_DIR = DATA_DIR / "extracted_tables"
OUTPUT_TEXT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_IMG_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_TABLE_DIR.mkdir(parents=True, exist_ok=True)


