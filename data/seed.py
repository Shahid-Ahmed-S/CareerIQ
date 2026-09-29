"""
Seed the database with sample skills, jobs, and demo users.
Run: python3 data/seed.py
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.extensions import db, bcrypt
from app.models.models import User, Profile, Skill, Job, JobSkill

app = create_app("development")

SKILLS = [
    ("Python","programming"),("JavaScript","programming"),("TypeScript","programming"),
    ("Java","programming"),("Go","programming"),("React","frontend"),("Vue.js","frontend"),
    ("Next.js","frontend"),("Node.js","backend"),("Flask","backend"),("Django","backend"),
    ("FastAPI","backend"),("Spring Boot","backend"),("GraphQL","backend"),("REST APIs","backend"),
    ("SQL","database"),("PostgreSQL","database"),("MySQL","database"),("MongoDB","database"),
    ("Redis","database"),("Elasticsearch","database"),("Docker","devops"),("Kubernetes","devops"),
    ("AWS","devops"),("GCP","devops"),("Azure","devops"),("Terraform","devops"),("CI/CD","devops"),
    ("Linux","tools"),("Git","tools"),("Machine Learning","ai-ml"),("Deep Learning","ai-ml"),
    ("NLP","ai-ml"),("PyTorch","ai-ml"),("TensorFlow","ai-ml"),("LLMs","ai-ml"),
    ("Data Analysis","data"),("Pandas","data"),("NumPy","data"),("Spark","data"),
    ("Tableau","data"),("Power BI","data"),("Agile","soft-skills"),("Scrum","soft-skills"),
]

JOBS = [
    {"title":"Senior Backend Engineer","company":"Stripe","location":"San Francisco, USA",
     "job_type":"full-time","experience_level":"senior","salary_min":160000,"salary_max":220000,
     "description":"Build and scale Stripe's payment infrastructure using Python and distributed systems.",
     "skills":[("python",3,True),("flask",2,True),("postgresql",3,True),("redis",2,True),
               ("docker",2,True),("aws",2,True),("rest apis",3,True),("git",2,True)]},
    {"title":"ML Engineer","company":"DeepMind","location":"London, UK",
     "job_type":"full-time","experience_level":"senior","salary_min":120000,"salary_max":180000,
     "description":"Research and deploy large-scale ML models. Work on cutting-edge AI research.",
     "skills":[("python",4,True),("machine learning",4,True),("deep learning",3,True),
               ("pytorch",3,True),("docker",2,True),("kubernetes",2,False),("git",2,True)]},
    {"title":"Full Stack Developer","company":"Shopify","location":"Remote",
     "job_type":"full-time","experience_level":"mid","salary_min":110000,"salary_max":150000,
     "description":"Build full-stack features for Shopify's merchant platform.",
     "skills":[("javascript",3,True),("typescript",2,True),("react",3,True),
               ("node.js",2,True),("postgresql",2,True),("rest apis",2,True),("git",2,True)]},
    {"title":"Data Scientist","company":"Netflix","location":"Los Angeles, USA",
     "job_type":"full-time","experience_level":"mid","salary_min":130000,"salary_max":170000,
     "description":"Build recommendation systems and analyse user behaviour at scale.",
     "skills":[("python",3,True),("machine learning",3,True),("sql",3,True),
               ("pandas",3,True),("numpy",2,True),("spark",2,False),("tableau",1,False)]},
    {"title":"Frontend Engineer","company":"Figma","location":"Remote",
     "job_type":"full-time","experience_level":"mid","salary_min":120000,"salary_max":160000,
     "description":"Build the Figma design editor UI with React and WebGL.",
     "skills":[("javascript",4,True),("typescript",3,True),("react",4,True),
               ("next.js",2,False),("git",2,True),("rest apis",2,True)]},
    {"title":"DevOps Engineer","company":"HashiCorp","location":"Remote",
     "job_type":"full-time","experience_level":"senior","salary_min":140000,"salary_max":190000,
     "description":"Manage cloud infrastructure and CI/CD pipelines at scale.",
     "skills":[("docker",3,True),("kubernetes",3,True),("terraform",3,True),
               ("aws",3,True),("ci/cd",3,True),("linux",2,True),("python",1,False)]},
    {"title":"Backend Python Developer","company":"Twilio","location":"Remote",
     "job_type":"full-time","experience_level":"mid","salary_min":100000,"salary_max":140000,
     "description":"Build communication APIs using Python and Flask.",
     "skills":[("python",3,True),("flask",2,True),("postgresql",2,True),
               ("rest apis",2,True),("redis",1,False),("docker",1,False)]},
    {"title":"Data Engineer","company":"Snowflake","location":"New York, USA",
     "job_type":"full-time","experience_level":"mid","salary_min":120000,"salary_max":160000,
     "description":"Build and maintain large-scale data pipelines.",
     "skills":[("python",3,True),("sql",3,True),("spark",2,True),("aws",2,True),
               ("docker",1,False),("pandas",2,True),("git",2,True)]},
    {"title":"iOS Developer","company":"Apple","location":"Cupertino, USA",
     "job_type":"full-time","experience_level":"senior","salary_min":170000,"salary_max":230000,
     "description":"Build world-class iOS features used by billions of users.",
     "skills":[("swift",4,True),("git",2,True),("rest apis",2,True)]},
    {"title":"Entry Level Frontend Developer","company":"Canva","location":"Sydney, Australia",
     "job_type":"full-time","experience_level":"entry","salary_min":65000,"salary_max":85000,
     "description":"Build Canva's design tools with React and TypeScript.",
     "skills":[("javascript",2,True),("react",2,True),("typescript",1,True),
               ("git",1,True),("rest apis",1,True)]},
    {"title":"NLP Research Engineer","company":"Anthropic","location":"San Francisco, USA",
     "job_type":"full-time","experience_level":"senior","salary_min":180000,"salary_max":300000,
     "description":"Research and develop large language model capabilities.",
     "skills":[("python",4,True),("machine learning",4,True),("nlp",4,True),
               ("deep learning",4,True),("pytorch",3,True),("llms",3,True)]},
    {"title":"Backend Engineer (Go)","company":"Uber","location":"Amsterdam, Netherlands",
     "job_type":"full-time","experience_level":"mid","salary_min":90000,"salary_max":130000,
     "description":"Build high-performance backend services in Go for Uber's platform.",
     "skills":[("go",3,True),("postgresql",2,True),("redis",2,True),
               ("docker",2,True),("kubernetes",1,False),("rest apis",2,True)]},
]

DEMO_USERS = [
    {"full_name":"Alex Johnson","email":"alex@demo.com","password":"demo123",
     "headline":"Senior Full Stack Engineer","location":"San Francisco, USA",
     "current_role":"Full Stack Engineer","desired_role":"Engineering Manager",
     "skills":[("Python",3),("JavaScript",3),("React",3),("Node.js",2),("PostgreSQL",2)]},
    {"full_name":"Priya Sharma","email":"priya@demo.com","password":"demo123",
     "headline":"Data Scientist | ML Enthusiast","location":"Bangalore, India",
     "current_role":"Data Scientist","desired_role":"ML Engineer",
     "skills":[("Python",4),("Machine Learning",3),("Pandas",3),("SQL",3),("TensorFlow",2)]},
    {"full_name":"TechCorp Recruiter","email":"recruiter@techcorp.com","password":"demo123",
     "role":"recruiter","headline":"Talent Acquisition at TechCorp","location":"New York, USA",
     "current_role":"Senior Recruiter","desired_role":"","skills":[]},
]


def seed():
    with app.app_context():
        db.create_all()

        # Skills
        skill_map = {}
        for name, category in SKILLS:
            norm  = name.lower()
            skill = Skill.query.filter_by(normalized_name=norm).first()
            if not skill:
                skill = Skill(name=name, normalized_name=norm, category=category)
                db.session.add(skill)
                db.session.flush()
            skill_map[norm] = skill
        db.session.commit()
        print(f"✓ {len(skill_map)} skills seeded")

        # Jobs
        jcount = 0
        for jd in JOBS:
            if Job.query.filter_by(title=jd["title"], company=jd["company"]).first():
                continue
            job = Job(title=jd["title"], company=jd["company"], location=jd["location"],
                      job_type=jd["job_type"], experience_level=jd["experience_level"],
                      description=jd["description"],
                      salary_min=jd["salary_min"], salary_max=jd["salary_max"])
            db.session.add(job); db.session.flush()
            for skey, level, required in jd["skills"]:
                skill = skill_map.get(skey)
                if skill:
                    db.session.add(JobSkill(job_id=job.id, skill_id=skill.id,
                                            required_level=level, is_required=required))
            jcount += 1
        db.session.commit()
        print(f"✓ {jcount} jobs seeded")

        # Demo users
        ucount = 0
        for ud in DEMO_USERS:
            if User.query.filter_by(email=ud["email"]).first():
                continue
            hashed = bcrypt.generate_password_hash(ud["password"]).decode("utf-8")
            user   = User(email=ud["email"], password_hash=hashed,
                          full_name=ud["full_name"],
                          role=ud.get("role","user"), email_verified=True)
            db.session.add(user); db.session.flush()
            db.session.add(Profile(user_id=user.id,
                                   headline=ud.get("headline",""),
                                   location=ud.get("location",""),
                                   current_role=ud.get("current_role",""),
                                   desired_role=ud.get("desired_role","")))
            for sname, level in ud.get("skills",[]):
                norm  = sname.lower()
                skill = skill_map.get(norm)
                if skill:
                    from app.models.models import UserSkill
                    db.session.add(UserSkill(user_id=user.id, skill_id=skill.id,
                                            proficiency_level=level))
            ucount += 1
        db.session.commit()
        print(f"✓ {ucount} demo users seeded")
        print("\n✅ Seeding complete!")
        print("\nDemo accounts:")
        print("  alex@demo.com     / demo123  (job seeker)")
        print("  priya@demo.com    / demo123  (job seeker)")
        print("  recruiter@techcorp.com / demo123  (recruiter)")


if __name__ == "__main__":
    seed()
