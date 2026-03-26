from __future__ import annotations

import os
import tempfile
from typing import Any, Dict, List

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent import analyze_skill_gap, generate_job_listings, optimise_cv, parse_cv_with_ai, prepare_interview_questions
from parser import extract_text_from_docx, extract_text_from_pdf


class JobSearchRequest(BaseModel):
    profile: Dict[str, Any]
    job_title: str
    location: str = ""


class TargetJobRequest(BaseModel):
    profile: Dict[str, Any]
    target_job: Dict[str, Any]


app = FastAPI(title="NextRole API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _extract_text(temp_path: str, filename: str) -> str:
    lower_name = filename.lower()

    if lower_name.endswith(".pdf"):
        return extract_text_from_pdf(temp_path)
    if lower_name.endswith(".docx"):
        return extract_text_from_docx(temp_path)

    raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported.")


@app.get("/api/health")
async def health_check() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/api/parse-cv")
async def parse_cv(file: UploadFile = File(...)) -> Dict[str, Any]:
    if not file.filename:
        raise HTTPException(status_code=400, detail="A file name is required.")

    if not file.filename.lower().endswith((".pdf", ".docx")):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported.")

    suffix = os.path.splitext(file.filename)[1]

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(await file.read())
        temp_path = temp_file.name

    try:
        extracted_text = _extract_text(temp_path, file.filename)
        if not extracted_text.strip():
            raise HTTPException(status_code=400, detail="We could not extract readable text from that file.")

        return parse_cv_with_ai(extracted_text)
    finally:
        try:
            os.unlink(temp_path)
        except FileNotFoundError:
            pass


@app.post("/api/job-search")
async def job_search(payload: JobSearchRequest) -> List[Dict[str, Any]]:
    if not payload.job_title.strip():
        raise HTTPException(status_code=400, detail="A job title is required.")

    return generate_job_listings(payload.profile, payload.job_title.strip(), payload.location.strip())


@app.post("/api/skill-gap")
async def skill_gap(payload: TargetJobRequest) -> Dict[str, Any]:
    return analyze_skill_gap(payload.profile, payload.target_job)


@app.post("/api/optimise-cv")
async def optimise_cv_endpoint(payload: TargetJobRequest) -> Dict[str, Any]:
    return optimise_cv(payload.profile, payload.target_job)


@app.post("/api/interview-prep")
async def interview_prep(payload: TargetJobRequest) -> List[Dict[str, Any]]:
    return prepare_interview_questions(payload.profile, payload.target_job)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
