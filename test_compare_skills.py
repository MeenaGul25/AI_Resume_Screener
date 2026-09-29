from app.services.skill_extractor import compare_skills

resume_text = """
Marketing Executive

Skills:
Communication
Customer Relationship Management
Customer Service
Data Analysis
Market Research
Project Management
Report
Social Media Management
Media Management
Email
"""

job_description_text = """
Marketing Executive

Required Skills:
Communicate with Customers
Implement Marketing Strategies
Maintain Relationships with Customers
Communication
Customer Service
Data Analysis
Market Research
Project Management
Report
"""

result = compare_skills(
    resume_text,
    job_description_text
)

print("\n========== COMPARE SKILLS RESULT ==========")

print("\nResume Skills:")
for skill in result["resume_skills"]:
    print("-", skill)

print("\nRequired Skills:")
for skill in result["required_skills"]:
    print("-", skill)

print("\nMatched Skills:")
for skill in result["matched_skills"]:
    print("-", skill)

print("\nMissing Skills:")
for skill in result["missing_skills"]:
    print("-", skill)

print("\nSemantic Matches:")
for match in result["semantic_matches"]:
    print(
        "-",
        match["required_skill"],
        "->",
        match["matched_skill"],
        f'({match["similarity"]}%)'
    )

print("\nSkills Score:")
print(result["skills_score"])

print("============================================")