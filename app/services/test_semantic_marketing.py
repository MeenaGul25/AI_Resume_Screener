from app.services.esco_loader import (
    get_esco_skill_variants
)
from app.services.skill_extractor import (
    extract_skills
)

from app.services.semantic_matcher import (
    calculate_skill_semantic_similarity
)


####
print("\nESCO SKILL VARIANT TEST")
print("------------------------")

test_skill = "customer relationship management"

variants = get_esco_skill_variants(
    test_skill
)

print("\nVariants for:")
print(test_skill)

for variant in variants:
    print("-", variant)
#####

resume = """
Rehana Jameel
Islamabad

Marketing Specialist with 3 years of experience.

Digital Growth Agency
2022 - Present

Developed and implemented digital marketing campaigns.
Managed social media marketing.
Created content.
Conducted market research.
Analyzed campaign and customer data.
Prepared marketing reports.
Developed marketing strategies.
Communicated with customers.
Provided customer service.
Maintained positive customer relationships.
Coordinated projects.
Performed data analysis.

Junior Marketing Executive
2021 - 2022

Worked on social media marketing.
Developed marketing strategies.
Performed competitor and market research.
Created marketing content.
Handled customer communication.
Prepared marketing reports.
Assisted with project planning.

Skills:
Digital Marketing
Social Media Marketing
Marketing Strategy
Market Research
Customer Service
Communication
Data Analysis
Project Management
Content Creation
Campaign Management
CRM
Excel
"""


job_description = """
Digital Marketing Specialist
BrightWave Solutions
Islamabad

Requirements:

Bachelor's degree in Marketing, Business, or Communications.

2+ years of experience in digital marketing.

Required skills:
Social media marketing
Digital marketing strategies
Communication
Customer service
Market research
Data analysis
Marketing reports
Project management

Responsibilities:

Develop and implement digital marketing campaigns.
Manage social media.
Create content.
Conduct market research.
Analyze campaigns and data.
Prepare marketing reports.
Develop marketing strategies.
Communicate with customers.
Maintain customer relationships.
Collaborate with sales and creative teams.
"""


resume_skills = set(
    extract_skills(resume)
)

required_skills = set(
    extract_skills(job_description)
)


print("\nACTUAL MARKETING SEMANTIC SKILL TEST")
print("---------------------------------------")

print("\nResume Skills:")
for skill in sorted(resume_skills):
    print("-", skill)


print("\nRequired Skills:")
for skill in sorted(required_skills):
    print("-", skill)


# Only compare skills that were not already
# exact matches.
unmatched_resume_skills = (
    resume_skills - required_skills
)

unmatched_required_skills = (
    required_skills - resume_skills
)


print("\nUnmatched Resume Skills:")
for skill in sorted(unmatched_resume_skills):
    print("-", skill)


print("\nUnmatched Required Skills:")
for skill in sorted(unmatched_required_skills):
    print("-", skill)


result = calculate_skill_semantic_similarity(
    unmatched_resume_skills,
    unmatched_required_skills
)


print("\nSemantic Matches:")

for match in result["matched_skills"]:

    print(
        f"- Required: {match['required_skill']}"
    )

    print(
        f"  Resume:   {match['matched_skill']}"
    )

    print(
        f"  Similarity: {match['similarity']}%"
    )


print("\nStill Missing Skills:")

for skill in result["missing_skills"]:
    print("-", skill)


print(
    "\nSemantic Skill Score:",
    result["semantic_skill_score"],
    "%"
)