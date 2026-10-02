import re
import spacy

from app.utils.skills import SKILLS
from app.services.esco_loader import build_esco_skill_dictionary
from app.services.semantic_matcher import (
    calculate_skill_semantic_similarity,
    get_semantic_skill_candidates
)

nlp = spacy.load("en_core_web_sm")

# Load ESCO skills once when the application starts.
ESCO_SKILLS = build_esco_skill_dictionary()

def normalize_skill_name(skill):
    """
    Normalize skill names so that different but equivalent
    representations can be matched consistently.
    """

    skill = skill.strip().lower()

    normalization_map = {
        # Programming
        "python": "python",
        "python (computer programming)": "python",

        # Accounting / Finance
        "prepare financial statements": "financial statements",
        "prepared financial statements": "financial statements",
        "preparing financial statements": "financial statements",

        "create a financial report": "financial reporting",
        "create financial reports": "financial reporting",
        "financial report": "financial reporting",
        "financial reports": "financial reporting",

        # Common variations
        "financial statement preparation": "financial statements",
        "financial statement analysis": "financial analysis",
        "analyze financial statements": "financial analysis",

        # Communication
        "written communication": "communication",
        "verbal communication": "communication",

        # Customer service
        "customer support": "customer service",
        "customer care": "customer service",
    }

    return normalization_map.get(skill, skill)

def normalize_text_for_skill_matching(text):
    """
    Normalize text before skill matching.

    This handles common grammatical variations such as:
    prepare -> prepared
    preparing -> prepare

    It also normalizes whitespace and punctuation.
    """

    if not text:
        return ""

    text = text.lower()

    # Normalize common verb forms.
    replacements = {
        "prepared": "prepare",
        "preparing": "prepare",
        "prepares": "prepare",

        "created": "create",
        "creating": "create",
        "creates": "create",

        "analyzed": "analyze",
        "analysed": "analyze",
        "analyzing": "analyze",
        "analysing": "analyze",

        "managed": "manage",
        "managing": "manage",
        "manages": "manage",

        "developed": "develop",
        "developing": "develop",
        "develops": "develop",

        "reported": "report",
        "reporting": "report",
        "reports": "report",

        "maintained": "maintain",
        "maintaining": "maintain",
        "maintains": "maintain",
    }

    for old, new in replacements.items():
        text = re.sub(
            r"\b" + re.escape(old) + r"\b",
            new,
            text
        )

    # Normalize whitespace.
    text = re.sub(r"\s+", " ", text)

    return text.strip()

def extract_candidate_phrases(text):
    """
    Extract conservative multi-word skill/competency candidates
    from resume text using spaCy noun chunks.
    """

    if not text:
        return []

    # -------------------------------------------------
    # 1. Normalize PDF text
    # -------------------------------------------------

    text = re.sub(r"\s+", " ", text).strip()

    # -------------------------------------------------
    # 2. Process with spaCy
    # -------------------------------------------------

    doc = nlp(text)

    candidates = set()

    ignored_phrases = {
        "professional summary",
        "professional experience",
        "job description",
        "job summary",
        "education",
        "skills",
        "responsibilities",
        "responsibility",
        "experience",
    }

    generic_words = {
        "year", "years",
        "month", "months",
        "company",
        "client", "clients",
        "business",
        "people", "person",
        "work",
        "role", "position",
        "experience",
        "summary",
        "education",
        "skill", "skills",
        "responsibility", "responsibilities",
    }

    # Words that normally indicate that the phrase
    # is describing an action rather than naming a skill.
    action_words = {
        "analyze",
        "analyzed",
        "analysed",
        "analyzing",
        "analyse",
        "prepare",
        "prepared",
        "preparing",
        "perform",
        "performed",
        "performing",
        "manage",
        "managed",
        "managing",
        "maintain",
        "maintained",
        "maintaining",
        "use",
        "used",
        "using",
        "assist",
        "assisted",
        "assisting",
        "process",
        "processed",
        "processing",
        "create",
        "created",
        "creating",
        "support",
        "supported",
        "supporting",
        "communicate",
        "communicated",
        "communicating",
    }

    for chunk in doc.noun_chunks:

        phrase = chunk.text.strip().lower()

        phrase = re.sub(
            r"^[^\w+#./-]+|[^\w+#./-]+$",
            "",
            phrase
        )

        phrase = re.sub(r"\s+", " ", phrase)

        if not phrase:
            continue

        if phrase in ignored_phrases:
            continue

        words = phrase.split()

        # Only multi-word phrases
        if len(words) < 2:
            continue

        # Reject phrases containing numbers
        if any(re.search(r"\d", word) for word in words):
            continue

        # Reject phrases beginning with an action/verb
        if words[0] in action_words:
            continue

        # Reject phrases containing obvious action verbs
        if any(word in action_words for word in words):
            continue

        # Reject phrases made entirely from generic words
        if all(word in generic_words for word in words):
            continue

        # Reject obvious person-name/profile chunks
        profile_words = {
            "professional",
            "summary",
            "accountant",
            "name",
            "present",
        }

        if any(word in profile_words for word in words):
            continue

        # Reject fragments ending with punctuation
        # or containing broken comma structures.
        if "," in phrase:
            continue

        candidates.add(phrase)

    return sorted(candidates)


def find_esco_candidates(phrases):
    """
    Generate conservative ESCO candidates.

    Candidates are generated using:
    1. Exact phrase matches.
    2. Strong overlap involving at least one
       domain-specific word.

    Generic words such as financial, data,
    planning, analysis, etc. are not enough
    to create an ESCO candidate.
    """

    if not phrases:
        return []

    candidates = {}

    generic_words = {
        "data",
        "records",
        "record",
        "report",
        "reports",
        "analysis",
        "analyses",
        "financial",
        "finance",
        "business",
        "information",
        "communication",
        "service",
        "services",
        "customer",
        "customers",
        "technology",
        "systems",
        "system",
        "process",
        "processes",
        "planning",
        "management",
        "managements",
        "skills",
        "skill",
        "work",
        "working",
        "operations",
        "operation"
    }

    for phrase in phrases:

        phrase = phrase.strip().lower()

        if not phrase:
            continue

        phrase_words = set(phrase.split())

        if len(phrase_words) < 2:
            continue

        for esco_label, skill_data in ESCO_SKILLS.items():

            esco_label = esco_label.strip().lower()

            if not esco_label:
                continue

            label_words = set(esco_label.split())

            if len(label_words) < 2:
                continue

            # -----------------------------------------
            # EXACT MATCH
            # -----------------------------------------

            if phrase == esco_label:

                preferred_label = (
                    skill_data["preferred_label"]
                    .strip()
                    .lower()
                )

                candidates[preferred_label] = {
                    "preferred_label": skill_data["preferred_label"],
                    "phrase": phrase,
                    "overlap": sorted(phrase_words),
                    "match_type": "exact"
                }

                continue

            # -----------------------------------------
            # WORD OVERLAP
            # -----------------------------------------

            overlap = phrase_words & label_words

            if len(overlap) < 2:
                continue

            # At least one overlapping word must
            # be domain-specific.
            meaningful_overlap = {
                word
                for word in overlap
                if word not in generic_words
                and len(word) >= 5
            }

            if not meaningful_overlap:
                continue

            phrase_coverage = (
                len(overlap) / len(phrase_words)
            )

            label_coverage = (
                len(overlap) / len(label_words)
            )

            strong_overlap = (
                phrase_coverage >= 0.75
                and label_coverage >= 0.50
            )

            if not strong_overlap:
                continue

            preferred_label = (
                skill_data["preferred_label"]
                .strip()
                .lower()
            )

            candidates[preferred_label] = {
                "preferred_label": skill_data["preferred_label"],
                "phrase": phrase,
                "overlap": sorted(overlap),
                "match_type": "overlap"
            }

    return list(candidates.values())

def extract_skills(text):
    """
    Extract skills from text using both:

    1. Existing manually defined CS/IT skills
    2. ESCO multi-domain skills

    Returns a sorted list of canonical skill names.
    """

    if not text:
        return []

    original_text = text.lower()
    text = normalize_text_for_skill_matching(text)
    found_skills = set()

    # -------------------------------------------------
    # 1. Existing manually defined skills
    # -------------------------------------------------

    for skill, variations in SKILLS.items():

        for variation in variations:

            variation = variation.strip().lower()

            if not variation:
                continue

            pattern = r"\b" + re.escape(variation) + r"\b"

            if re.search(pattern, text):
                found_skills.add(skill)
                break

    # -------------------------------------------------
    # 2. ESCO preferred skills
    # -------------------------------------------------

    for skill_term, skill_data in ESCO_SKILLS.items():
        skill_term = skill_term.strip().lower()

        if not skill_term:
            continue

        preferred_label = (
            skill_data.get("preferred_label", "")
            .strip()
            .lower()
        )

        # Only use the official ESCO preferred label.
        if skill_term != preferred_label:
            continue

        pattern = r"\b" + re.escape(skill_term) + r"\b"

        if re.search(pattern, original_text):
            found_skills.add(skill_term)


    # --------------------------------------------------
    # 3. Candidate phrase extraction
    # --------------------------------------------------

    candidate_phrases = extract_candidate_phrases(text)

  

    # --------------------------------------------------
    # 4. ESCO semantic evidence
    # --------------------------------------------------

    semantic_skill_candidates = get_semantic_skill_candidates(
        candidate_phrases,
        ESCO_SKILLS,
        threshold=0.70
    )

    # Add only semantically validated resume phrases.
    # The original resume phrase is preserved.
    for candidate in semantic_skill_candidates:

        skill = candidate["skill"].strip().lower()

        if not skill:
            continue

        found_skills.add(skill)

    # ESCO semantic candidates are supporting evidence.
    # The original resume phrase is preserved rather than
    # replacing it with an ESCO action-oriented label.
    # ESCO semantic candidates are used as supporting evidence.
    # Do not directly add ESCO preferred labels to found_skills,
    # because ESCO labels may be action-oriented concepts such as
    # "use spreadsheets software" or "follow up accounts receivables".
    # -------------------------------------------------
    # Normalize obvious duplicate representations
    # -------------------------------------------------

    normalized_skills = set()

    for skill in found_skills:
        normalized_skills.add(
            normalize_skill_name(skill)
        )

    return sorted(normalized_skills)

    

def compare_skills(resume_text, job_description_text):
    """
    Compare skills found in a resume against  
    skills required by a job description.

    Uses:
    1. ESCO/exact skill matching
    2. SBERT semantic skill matching
    """

    resume_skills = set(
        extract_skills(resume_text)
    )

    required_skills = set(
        extract_skills(job_description_text)
    )

    # -------------------------------------------------
    # 1. Exact / ESCO skill matching
    # -------------------------------------------------

    exact_matched_skills = (
        resume_skills & required_skills
    )

    unmatched_required_skills = (
        required_skills - resume_skills
    )

    unmatched_resume_skills = (
        resume_skills - required_skills
    )

    # -------------------------------------------------
    # 2. Semantic matching for unmatched skills
    # -------------------------------------------------

    semantic_result = calculate_skill_semantic_similarity(
        unmatched_resume_skills,
        unmatched_required_skills
    )

    semantic_matches = semantic_result[
        "matched_skills"
    ]

    semantic_missing = semantic_result[
        "missing_skills"
    ]

    # -------------------------------------------------
    # 3. Combine exact and semantic matches
    # -------------------------------------------------

    matched_skills = set(
        exact_matched_skills
    )

    for match in semantic_matches:

        matched_skills.add(
            match["required_skill"]
        )

    missing_skills = set(
        semantic_missing
    )

    # -------------------------------------------------
    # 4. Calculate final skills score
    # -------------------------------------------------

    if required_skills:

        skills_score = (
            len(matched_skills)
            / len(required_skills)
        ) * 100

    else:

        skills_score = 0.0

    return {
        "resume_skills":
            sorted(resume_skills),

        "required_skills":
            sorted(required_skills),

        "matched_skills":
            sorted(matched_skills),

        "missing_skills":
            sorted(missing_skills),

        "semantic_matches":
            semantic_matches,

        "skills_score":
            round(skills_score, 2)
    }