from __future__ import annotations

import os
import tempfile
import json
import html
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st
from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parent
load_dotenv(ROOT_DIR / ".env")

# Ensure backend is importable in Streamlit Cloud and local environments
import sys
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

if "OPENAI_API_KEY" not in os.environ:
    try:
        secret_key = st.secrets.get("OPENAI_API_KEY")
    except Exception:
        secret_key = None
    if secret_key:
        os.environ["OPENAI_API_KEY"] = secret_key

from backend.agent import analyze_skill_gap, generate_job_listings, get_runtime_status, optimise_cv, parse_cv_with_ai, prepare_interview_questions
from backend.parser import extract_text_from_docx, extract_text_from_pdf
