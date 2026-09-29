import re


def extract_experience_years(text):
    """
    Extract the candidate's approximate years
    of professional experience from resume text.
    """

    if not text:
        return 0.0

    text = text.lower()

    patterns = [
        r'(\d+(?:\.\d+)?)\+?\s*years?\s+of\s+experience',
        r'(\d+(?:\.\d+)?)\+?\s*years?\s+experience',
        r'experience\s*[:\-]?\s*(\d+(?:\.\d+)?)\+?\s*years?'
    ]

    years_found = []

    for pattern in patterns:

        matches = re.findall(
            pattern,
            text
        )

        for match in matches:

            try:
                years_found.append(
                    float(match)
                )

            except ValueError:
                pass

    if not years_found:
        return 0.0

    return max(years_found)


def extract_required_experience(job_description):
    """
    Extract the minimum required years of experience
    from a job description.

    Supports formats such as:
    - 2+ years of experience
    - 3 years of experience
    - 2 years experience
    - at least 2 years of experience
    - minimum 2 years of experience
    - minimum of 2 years of experience
    - 2-4 years of experience
    """

    if not job_description:
        return 0.0

    text = job_description.lower()

    experience_values = []

    # Pattern 1:
    # "2+ years of experience"
    matches = re.findall(
        r'\b(\d+(?:\.\d+)?)\s*\+\s*(?:years?|yrs?)\b',
        text
    )

    for match in matches:
        experience_values.append(float(match))

    # Pattern 2:
    # "at least 2 years"
    # "minimum 2 years"
    # "minimum of 2 years"
    matches = re.findall(
        r'\b(?:at least|minimum(?:\s+of)?)\s+'
        r'(\d+(?:\.\d+)?)\s*(?:years?|yrs?)\b',
        text
    )

    for match in matches:
        experience_values.append(float(match))

    # Pattern 3:
    # "2 years of experience"
    # "2 years experience"
    matches = re.findall(
        r'\b(\d+(?:\.\d+)?)\s*(?:years?|yrs?)'
        r'(?:\s+of)?\s+experience\b',
        text
    )

    for match in matches:
        experience_values.append(float(match))

    # Pattern 4:
    # "2-4 years of experience"
    # Use the lower value as the minimum requirement.
    matches = re.findall(
        r'\b(\d+(?:\.\d+)?)\s*[-–]\s*'
        r'(\d+(?:\.\d+)?)\s*(?:years?|yrs?)\b',
        text
    )

    for minimum, maximum in matches:
        experience_values.append(float(minimum))

    if experience_values:
        return max(experience_values)

    return 0.0

 
def compare_experience(
    resume_text,
    job_description_text
):
    """
    Compare candidate experience against
    the job requirement.
    """

    candidate_years = extract_experience_years(
        resume_text
    )

    required_years = extract_required_experience(
        job_description_text
    )

    if required_years == 0:
        meets_requirement = True
    else:
        meets_requirement = (
            candidate_years >= required_years
        )

    return {
        "candidate_years": candidate_years,
        "required_years": required_years,
        "meets_requirement": meets_requirement
    }

def extract_education(text):
    """
    Detect the highest/common education qualification
    mentioned in the candidate resume.

    Uses word-boundary matching to avoid false detections
    such as "MBA" being detected inside "Islamabad".
    """

    if not text:
        return None

    text = text.lower()

    def contains_term(term):
        """
        Check whether a term appears as a complete word/phrase
        instead of as part of another word.
        """

        pattern = r"\b" + re.escape(term.lower()) + r"\b"

        return re.search(pattern, text) is not None

    # --------------------------------------------------
    # PhD
    # --------------------------------------------------

    phd_terms = [
        "phd",
        "ph.d",
        "ph.d.",
        "doctorate",
        "doctor of philosophy"
    ]

    if any(contains_term(term) for term in phd_terms):
        return "phd"

    # --------------------------------------------------
    # Master's
    # --------------------------------------------------

    master_terms = [
        "master's",
        "masters",
        "master degree",
        "master's degree",
        "masters degree",
        "master of",
        "ms degree",
        "ms in",
        "ms",
        "m.s.",
        "m.s",
        "m.sc",
        "m.sc.",
        "msc",
        "mba",
        "mca",
        "meng",
        "m.eng",
        "master of business administration",
        "master of science",
        "master of arts",
        "master of engineering",
        "master of technology"
    ]

    if any(contains_term(term) for term in master_terms):
        return "master's"

    # --------------------------------------------------
    # Bachelor's
    # --------------------------------------------------

    bachelor_terms = [
        "bachelor's",
        "bachelors",
        "bachelor degree",
        "bachelor's degree",
        "bachelors degree",
        "bachelor of",
        "bs degree",
        "bs in",
        "bs",
        "b.s.",
        "b.s",
        "bsc",
        "b.sc",
        "b.sc.",
        "bba",
        "bcom",
        "b.com",
        "ba degree",
        "ba in",
        "b.a.",
        "b.e.",
        "be degree",
        "be in",
        "btech",
        "b.tech",
        "b.tech.",
        "bachelor of business administration",
        "bachelor of science",
        "bachelor of arts",
        "bachelor of commerce",
        "bachelor of engineering",
        "bachelor of technology",
        "bachelor of computer science"
    ]

    if any(contains_term(term) for term in bachelor_terms):
        return "bachelor's"

    # --------------------------------------------------
    # Associate
    # --------------------------------------------------

    associate_terms = [
        "associate degree",
        "associate's degree",
        "associates degree"
    ]

    if any(contains_term(term) for term in associate_terms):
        return "associate"

    # --------------------------------------------------
    # Diploma
    # --------------------------------------------------

    if contains_term("diploma"):
        return "diploma"

    return None

def extract_required_education(text):
    """
    Detect the education level required
    by the job description.
    """

    if not text:
        return None

    text = text.lower()

    if any(
        phrase in text
        for phrase in [
            "phd",
            "doctorate",
            "doctor of philosophy"
        ]
    ):
        return "phd"

    if any(
        phrase in text
        for phrase in [
            "master's degree",
            "masters degree",
            "master degree",
            "ms degree",
            "ms in"
        ]
    ):
        return "master's"

    if any(
        phrase in text
        for phrase in [
            "bachelor's degree",
            "bachelors degree",
            "bachelor degree",
            "bs degree",
            "bs in"
        ]
    ):
        return "bachelor's"

    if "associate degree" in text:
        return "associate"

    if "diploma" in text:
        return "diploma"

    return None

def compare_education(
    resume_text,
    job_description_text
):
    """
    Compare candidate education against
    the job requirement.
    """

    candidate_education = extract_education(
        resume_text
    )

    required_education = extract_required_education(
        job_description_text
    )

    priority = {
        "phd": 5,
        "master's": 4,
        "bachelor's": 3,
        "associate": 2,
        "diploma": 1
    }

    if required_education is None:

        meets_requirement = True

    elif candidate_education is None:

        meets_requirement = False

    else:

        meets_requirement = (
            priority[candidate_education]
            >= priority[required_education]
        )

    return {
        "candidate_education":
            candidate_education,

        "required_education":
            required_education,

        "meets_requirement":
            meets_requirement
    }

 

def analyze_candidate(
    resume_text,
    job_description_text
):
    """
    Perform experience and education analysis.
    """

    print("\n========== EDUCATION DEBUG ==========")
    print("Detected education:", extract_education(resume_text))
    print("Resume contains 'master':", "master" in resume_text.lower())
    print("Resume contains 'mba':", "mba" in resume_text.lower())
    print("Resume contains 'bba':", "bba" in resume_text.lower())
    print("Resume contains 'bachelor':", "bachelor" in resume_text.lower())
    print("=====================================\n")

    experience = compare_experience(
        resume_text,
        job_description_text
    )

    education = compare_education(
        resume_text,
        job_description_text
    )

    return {
        "experience": experience,
        "education": education
    }

def calculate_experience_score(
    candidate_years,
    required_years
):
    """
    Convert experience into a score from 0 to 100.
    """

    if required_years <= 0:
        return 100.0

    if candidate_years >= required_years:
        return 100.0

    score = (
        candidate_years / required_years
    ) * 100

    return round(score, 2)

def calculate_education_score(
    candidate_education,
    required_education
):
    """
    Convert education qualification into
    a score from 0 to 100.
    """

    if required_education is None:
        return 100.0

    if candidate_education is None:
        return 0.0

    priority = {
        "phd": 5,
        "master's": 4,
        "bachelor's": 3,
        "associate": 2,
        "diploma": 1
    }

    candidate_level = priority.get(
        candidate_education,
        0
    )

    required_level = priority.get(
        required_education,
        0
    )

    if candidate_level >= required_level:
        return 100.0

    return 0.0

def calculate_final_score(
    semantic_score,
    skills_score,
    tfidf_score,
    experience_score,
    education_score
):
    """
    Calculate the final candidate match score
    using weighted components.
    """

    final_score = (
        (semantic_score * 0.40)
        +
        (skills_score * 0.30)
        +
        (tfidf_score * 0.15)
        +
        (experience_score * 0.10)
        +
        (education_score * 0.05)
    )

    return round(final_score, 2)

def classify_candidate(score):
    """
    Classify candidate based on final match score.
    """

    if score >= 80:
        return "Strong Candidate"

    elif score >= 60:
        return "Moderate Candidate"

    else:
        return "Weak Candidate"
    

def get_hr_recommendation(score):
    """
    Generate an HR recommendation based on
    the candidate's final match score.
    """

    if score >= 80:
        return "Highly Recommended"

    elif score >= 65:
        return "Recommended"

    elif score >= 50:
        return "Consider"

    else:
        return "Not Recommended"
    
def generate_strengths_weaknesses(
    matched_skills,
    missing_skills,
    experience_analysis,
    education_analysis
):
    """
    Generate candidate strengths and weaknesses
    for HR review.
    """

    strengths = []
    weaknesses = []

    # Skills analysis
    if matched_skills:
        strengths.append(
            f"Matches {len(matched_skills)} required skill(s)."
        )

    if missing_skills:
        weaknesses.append(
            f"Missing {len(missing_skills)} required skill(s)."
        )

    # Experience analysis
    if experience_analysis["meets_requirement"]:
        strengths.append(
            "Meets the required experience."
        )
    else:
        weaknesses.append(
            "Does not meet the required experience."
        )

    # Education analysis
    if education_analysis["meets_requirement"]:
        strengths.append(
            "Meets the required education."
        )
    else:
        weaknesses.append(
            "Does not meet the required education."
        )

    return {
        "strengths": strengths,
        "weaknesses": weaknesses
    }

#testing

if __name__ == "__main__":

    test_cases = [
        "Islamabad, Pakistan",
        "Bachelor of Business Administration (BBA)",
        "Bachelor of Business Administration (BBA), Islamabad",
        "Master of Business Administration (MBA)",
        "MBA graduate working in Islamabad",
        "BS Computer Science"
    ]

    print("\nEDUCATION FALSE-DETECTION TEST")
    print("--------------------------------")

    for text in test_cases:
        print(f"{text} -> {extract_education(text)}")