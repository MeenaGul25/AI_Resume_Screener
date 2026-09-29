from app.services.skill_extractor import extract_skills

resume_text = """
Marketing Executive

Skills:
Communication
Customer Relationship Management
Customer Service
Market Analysis
Project Management
Report Facts
Statistics
Social Media Management
Media Planning
Marketing Principles
Electronic Communication
"""

skills = extract_skills(resume_text)

print("\n========== EXTRACTED SKILLS ==========")

for skill in skills:
    print("-", skill)

print("=======================================")