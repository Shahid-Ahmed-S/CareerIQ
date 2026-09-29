import re, os, logging
from app.extensions import db
from app.models.models import UserSkill, Job, JobSkill

logger = logging.getLogger(__name__)

PROFICIENCY = {0:"Not acquired",1:"Beginner",2:"Intermediate",3:"Advanced",4:"Expert"}
RESOURCES   = {
    "python":"https://docs.python.org/3/tutorial/",
    "javascript":"https://javascript.info",
    "react":"https://react.dev/learn",
    "sql":"https://www.w3schools.com/sql/",
    "machine learning":"https://www.coursera.org/learn/machine-learning",
    "docker":"https://docs.docker.com/get-started/",
    "aws":"https://aws.amazon.com/training/",
    "default":"https://www.coursera.org/search?query=",
}

KNOWN_SKILLS = {
    "python","javascript","typescript","java","go","rust","c++","c#","php","ruby",
    "react","vue","vue.js","angular","next.js","svelte","html","css","tailwind",
    "node.js","flask","django","fastapi","spring boot","express","graphql","rest apis",
    "sql","postgresql","mysql","mongodb","redis","elasticsearch","sqlite",
    "docker","kubernetes","aws","gcp","azure","terraform","ci/cd","linux","nginx",
    "machine learning","deep learning","nlp","pytorch","tensorflow","keras","scikit-learn",
    "pandas","numpy","spark","tableau","power bi","data analysis",
    "git","github","jira","agile","scrum","microservices",
}


# ─────────────────────────────────────────────
#  Skill Gap Analyzer
# ─────────────────────────────────────────────
class SkillGapAnalyzer:

    def analyze(self, user_id, target_role):
        user_map = {us.skill.normalized_name: us.proficiency_level
                    for us in db.session.query(UserSkill).join(UserSkill.skill)
                                .filter(UserSkill.user_id == user_id).all()}

        jobs = Job.query.filter(Job.title.ilike(f"%{target_role}%"),
                                Job.is_active == True).limit(20).all()
        if not jobs:
            return {"success": False, "error": f"No job postings found for '{target_role}'."}

        role_map = {}
        for job in jobs:
            for js in job.job_skills:
                key = js.skill.normalized_name
                if key not in role_map or js.required_level > role_map[key]["required_level"]:
                    role_map[key] = {"required_level": js.required_level,
                                     "is_required": js.is_required,
                                     "skill_name": js.skill.name}

        total_w, total_g = 0.0, 0.0
        gap_details = []
        for key, req in role_map.items():
            w        = 2.0 if req["is_required"] else 1.0
            ulevel   = user_map.get(key, 0)
            raw_gap  = max(0, req["required_level"] - ulevel)
            norm_gap = raw_gap / 4.0
            total_w += w; total_g += norm_gap * w
            res_url  = RESOURCES.get(key, RESOURCES["default"] + key.replace(" ","+"))
            gap_details.append({
                "skill": req["skill_name"], "required_level": req["required_level"],
                "required_label": PROFICIENCY[req["required_level"]],
                "user_level": ulevel, "user_label": PROFICIENCY.get(ulevel,"Not acquired"),
                "gap": raw_gap, "is_required": req["is_required"],
                "priority_score": round((norm_gap*w)/(total_w or 1), 4),
                "resource_url": res_url,
            })

        gap_details.sort(key=lambda x: x["priority_score"], reverse=True)
        overall = round(total_g / total_w, 4) if total_w else 0.0
        learning_path = [
            {"step": i+1, "skill": g["skill"],
             "current_label": g["user_label"], "target_label": g["required_label"],
             "resource_url":  g["resource_url"],
             "reason": f"You're at {g['user_label']} but {g['skill']} requires {g['required_label']}."}
            for i, g in enumerate(gap_details) if g["gap"] > 0
        ]
        return {"success": True, "target_role": target_role,
                "overall_gap_score": overall,
                "readiness_pct": round((1 - overall) * 100, 1),
                "gap_details": gap_details, "learning_path": learning_path}


# ─────────────────────────────────────────────
#  Recommendation Engine
# ─────────────────────────────────────────────
class RecommendationEngine:

    def recommend_jobs(self, user_id, top_n=10):
        user_map = {us.skill.normalized_name: us.proficiency_level
                    for us in db.session.query(UserSkill).join(UserSkill.skill)
                                .filter(UserSkill.user_id == user_id).all()}
        if not user_map: return []
        scored = []
        for job in Job.query.filter_by(is_active=True).all():
            score, reasons = self._score(user_map, job)
            if score > 0: scored.append({"job": job, "score": score, "reasons": reasons})
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_n]

    def _score(self, user_map, job):
        if not job.job_skills: return 0.0, []
        total_w, earned, reasons = sum(2.0 if js.is_required else 1.0 for js in job.job_skills), 0.0, []
        for js in job.job_skills:
            key = js.skill.normalized_name
            w   = 2.0 if js.is_required else 1.0
            ul  = user_map.get(key, 0)
            if ul == 0: continue
            if ul >= js.required_level:
                earned += w + (ul - js.required_level) * 0.25 * w
                reasons.append(f"Strong: {js.skill.name}")
            else:
                earned += w * (ul / js.required_level) * 0.5
                reasons.append(f"Partial: {js.skill.name}")
        return round(earned / total_w, 4) if total_w else 0.0, reasons[:4]

    def suggest_skills(self, user_id, top_n=5):
        have = {us.skill.normalized_name
                for us in db.session.query(UserSkill).join(UserSkill.skill)
                            .filter(UserSkill.user_id == user_id).all()}
        freq = {}
        for js in db.session.query(JobSkill).join(JobSkill.job).filter(Job.is_active == True).all():
            k = js.skill.normalized_name
            if k not in have:
                if k not in freq: freq[k] = {"name": js.skill.name, "count": 0}
                freq[k]["count"] += 1
        return sorted(freq.values(), key=lambda x: x["count"], reverse=True)[:top_n]


# ─────────────────────────────────────────────
#  Resume Parser
# ─────────────────────────────────────────────
EXPERIENCE_HDR = re.compile(
    r"(work experience|professional experience|experience|employment history|career history)",
    re.IGNORECASE)
STOP_HDR = re.compile(
    r"(education|certifications|projects|awards|publications|references|languages|interests)",
    re.IGNORECASE)
DATE_PAT = re.compile(
    r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[\s,]*\d{4}"
    r"|\d{4}\s*[-–]\s*(\d{4}|present|current|now)", re.IGNORECASE)


class ResumeParser:

    def parse(self, path):
        ext = os.path.splitext(path)[1].lower()
        if ext == ".pdf":   text = self._pdf(path)
        elif ext == ".docx": text = self._docx(path)
        else: return {"success": False, "error": "Upload PDF or DOCX."}
        if not text: return {"success": False, "error": "Could not extract text."}
        return {"success": True, "skills": self._skills(text),
                "experience": self._experience(text)}

    def _pdf(self, path):
        try:
            import fitz
            doc = fitz.open(path)
            t = "\n".join(p.get_text() for p in doc)
            doc.close(); return t
        except Exception as e:
            logger.error(e); return ""

    def _docx(self, path):
        try:
            from docx import Document
            return "\n".join(p.text for p in Document(path).paragraphs)
        except Exception as e:
            logger.error(e); return ""

    def _skills(self, text):
        tl = text.lower()
        found = []
        for s in KNOWN_SKILLS:
            if re.search(r'\b' + re.escape(s) + r'\b', tl):
                found.append({"name": s.title(), "normalized_name": s.lower(), "proficiency_level": 2})
        return sorted(found, key=lambda x: x["name"])

    def _experience(self, text):
        lines, exp, in_exp, cur = text.split("\n"), [], False, None
        for line in lines:
            s = line.strip()
            if not s: continue
            if EXPERIENCE_HDR.search(s) and len(s) < 60:
                in_exp = True; cur = None; continue
            if in_exp and STOP_HDR.search(s) and len(s) < 60:
                if cur: exp.append(cur)
                cur = None; in_exp = False; continue
            if not in_exp: continue
            if DATE_PAT.search(s):
                if cur: exp.append(cur)
                cur = {"title": DATE_PAT.sub("",s).strip(" –|-·•")[:120],
                       "company":"", "period": s, "description":""}
            elif cur:
                if not cur["company"] and len(s) < 80: cur["company"] = s
                else: cur["description"] += s + " "
        if cur: exp.append(cur)
        for e in exp: e["description"] = e["description"].strip()[:500]
        return exp[:10]


skill_gap_analyzer    = SkillGapAnalyzer()
recommendation_engine = RecommendationEngine()
resume_parser         = ResumeParser()
