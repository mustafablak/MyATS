from fastapi import FastAPI, UploadFile, File, Form
from typing import List
import pdfplumber
import io
from fastapi.middleware.cors import CORSMiddleware
import re
from sentence_transformers import SentenceTransformer, util

app = FastAPI(
    title="MyAPI",
    description="AI-Powered Dynamic CV Evaluation Engine",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ai_model = None
def extract_dynamic_keywords(text: str) -> list:
    stop_words = {
        "and", "or", "the", "for", "with", "from", "this", "that", "are", "you", "we", "our", 
        "in", "an", "as", "is", "of", "to", "on", "at", "by", "it", "be", "am", "was", "were",
        "has", "have", "had", "do", "does", "did", "but", "if", "not", "no", "can", "will", "a",
        "which", "who", "whom", "whose", "how", "what", "where", "when", "why", "their", "they",
        
        "ve", "veya", "ile", "için", "bir", "gibi", "olan", "olarak", "arayan", "arar", 
        "çok", "daha", "en", "iyi", "takım", "çalışma", "arkadaşı", "uzun", "dönem", "biz",
        
        "looking", "seeking", "experience", "developing", "modern", "applications", "candidate",
        "software", "using", "projects", "engineer", "frameworks", "development", "work", "skills",
        "requirements", "knowledge", "understanding", "good", "strong", "team", "years", "environment"
    }
    
    words = re.findall(r'\b[a-z0-9+#-]{2,}\b', text.lower())
    return list(set(word for word in words if word not in stop_words))

@app.on_event("startup")
async def load_model():
    global ai_model
    ai_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    print("AI model loaded successfully! 🚀")

@app.get("/")
async def root():
    return {"status": "success", "message": "MyAPI is running!"}

@app.post("/evaluate-cv/")
async def evaluate_cv(
    job_description: str = Form(..., description="Job description text"),
    file: UploadFile = File(...)
):
    if not file.filename.endswith(".pdf"):
        return {"error": "Please upload a PDF file."}
    
    try:
        contents = await file.read()
        cv_text = ""
        with pdfplumber.open(io.BytesIO(contents)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    cv_text += text + "\n"
        
        cv_embedding = ai_model.encode(cv_text, convert_to_tensor=True)
        job_embedding = ai_model.encode(job_description, convert_to_tensor=True)
        similarity = util.cos_sim(cv_embedding, job_embedding).item()
        semantic_score = max(0, similarity * 100)
        required_skills = extract_dynamic_keywords(job_description)
        cv_lower = cv_text.lower()
        matched_skills = [skill for skill in required_skills if skill in cv_lower]
        
        if len(required_skills) > 0:
            keyword_score = (len(matched_skills) / len(required_skills)) * 100
        else:
            keyword_score = 0
            
        match_score = round((semantic_score * 0.3) + (keyword_score * 0.7), 2)
        
        if match_score >= 50:
            status = "Strong Candidate 🌟"
        elif match_score >= 25:
            status = "Potential Candidate 👍"
        else:
            status = "Weak Match ❌"

        return {
            "candidate_file": file.filename,
            "match_score": f"{match_score}%",
            "evaluation_status": status,
            "matched_skills": matched_skills,
            "cv_character_count": len(cv_text)
        }
        
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}

@app.post("/evaluate-batch/")
async def evaluate_batch(
    job_description: str = Form(..., description="Job description text"),
    files: List[UploadFile] = File(..., description="Select multiple PDF files")
):
    results = []
    
    jd_embedding = ai_model.encode(job_description, convert_to_tensor=True)
    required_skills = extract_dynamic_keywords(job_description)

    for file in files:
        if not file.filename.endswith(".pdf"):
            continue 
        
        try:
            contents = await file.read()
            cv_text = ""
            with pdfplumber.open(io.BytesIO(contents)) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        cv_text += text + "\n"
            cv_lower = cv_text.lower()
            
            cv_embedding = ai_model.encode(cv_text, convert_to_tensor=True)
            similarity = util.cos_sim(cv_embedding, jd_embedding).item()
            semantic_score = max(0, similarity * 100)
            
            matched_skills = [skill for skill in required_skills if skill in cv_lower]
            keyword_score = (len(matched_skills) / max(1, len(required_skills))) * 100
            
            match_score = round((semantic_score * 0.3) + (keyword_score * 0.7), 2)
            
            if match_score >= 50:
                status = "Strong Candidate 🌟"
            elif match_score >= 25:
                status = "Potential Candidate 👍"
            else:
                status = "Weak Match ❌"

            results.append({
                "candidate_file": file.filename,
                "raw_score": match_score, 
                "match_score": f"{match_score}%",
                "evaluation_status": status,
                "matched_skills": matched_skills
            })
        except Exception:
            continue 

    ranked_results = sorted(results, key=lambda x: x["raw_score"], reverse=True)

    for rank, res in enumerate(ranked_results, 1):
        res["rank"] = rank
        del res["raw_score"]

    return {
        "total_evaluated_candidates": len(ranked_results),
        "leaderboard": ranked_results
    }