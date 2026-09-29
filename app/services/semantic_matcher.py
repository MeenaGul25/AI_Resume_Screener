import re

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from app.services.esco_loader import (
    get_esco_skill_variants
)

model = None


def get_model():
    global model

    if model is None:

        print("Loading SBERT model...")

        model = SentenceTransformer(
            "all-MiniLM-L6-v2"
        )

        print("SBERT model loaded successfully.")

    return model


def calculate_semantic_match_score(
    resume_text,
    job_description_text
):

    if not resume_text or not job_description_text:
        return 0.0

    # Load model only when needed
    sbert_model = get_model()

    # Generate embeddings
    resume_embedding = sbert_model.encode(
        resume_text,
        convert_to_numpy=True
    )

    job_embedding = sbert_model.encode(
        job_description_text,
        convert_to_numpy=True
    )

    # Calculate cosine similarity
    similarity = cosine_similarity(
        [resume_embedding],
        [job_embedding]
    )[0][0]

    # Convert to percentage
    score = similarity * 100

    return round(score, 2)

def get_meaningful_words(text):
    if not text:
        return set()

    stop_words = {
        "a", "an", "and", "the", "of", "to", "in", "on",
        "for", "with", "by", "from", "at", "as", "is",
        "are", "be", "or"
    }

    words = re.findall(
        r"\b[a-zA-Z]{3,}\b",
        text.lower()
    )

    normalized_words = set()

    plural_map = {
        "customers": "customer",
        "relationships": "relationship",
        "strategies": "strategy",
        "principles": "principle",
        "reports": "report",
        "skills": "skill",
        "services": "service",
        "systems": "system",
        "technologies": "technology",
        "applications": "application"
    }

    for word in words:

        if word in stop_words:
            continue

        word = plural_map.get(word, word)

        normalized_words.add(word)

    return normalized_words

def calculate_skill_semantic_similarity(
    resume_skills,
    required_skills,
    threshold=0.65
):
    """
    Compare resume skills with required skills using SBERT
    and ESCO skill variants.

    Stronger semantic matches are prioritized so that a
    resume skill is assigned to the most appropriate
    required skill.
    """

    if not resume_skills or not required_skills:
        return {
            "matched_skills": [],
            "missing_skills": list(required_skills),
            "semantic_skill_score": 0.0
        }

    sbert_model = get_model()

    resume_skills = list(resume_skills)
    required_skills = list(required_skills)

    # -------------------------------------------------
    # Generate all possible resume ↔ required matches
    # -------------------------------------------------

    possible_matches = []

    for required_skill in required_skills:

        required_variants = get_esco_skill_variants(
            required_skill
        )

        if not required_variants:
            required_variants = [required_skill]

        required_embeddings = sbert_model.encode(
            required_variants,
            convert_to_numpy=True
        )

        required_words = get_meaningful_words(
            required_skill
        )

        for resume_skill in resume_skills:

            resume_variants = get_esco_skill_variants(
                resume_skill
            )

            if not resume_variants:
                resume_variants = [resume_skill]

            resume_embeddings = sbert_model.encode(
                resume_variants,
                convert_to_numpy=True
            )

            similarity_matrix = cosine_similarity(
                required_embeddings,
                resume_embeddings
            )

            raw_similarity = similarity_matrix.max()

            resume_words = get_meaningful_words(
                resume_skill
            )

            lexical_overlap = (
                required_words & resume_words
            )

            has_lexical_evidence = (
                len(lexical_overlap) >= 1
                and any(
                    len(word) >= 8
                    for word in lexical_overlap
                )
            )

            strong_semantic_match = (
                raw_similarity >= 0.80
            )

            valid_match = (
                raw_similarity >= threshold
                and (
                    has_lexical_evidence
                    or strong_semantic_match
                )
            )

            if valid_match:

                possible_matches.append({
                    "required_skill": required_skill,
                    "matched_skill": resume_skill,
                    "similarity": raw_similarity,
                    "lexical": has_lexical_evidence
                })

    # -------------------------------------------------
    # Sort all possible matches by strongest similarity
    # -------------------------------------------------

    possible_matches.sort(
        key=lambda match: match["similarity"],
        reverse=True
    )

    # -------------------------------------------------
    # Assign each resume skill only once
    # -------------------------------------------------

    matched_skills = []
    matched_required_skills = set()
    used_resume_skills = set()

    for match in possible_matches:

        required_skill = match["required_skill"]
        resume_skill = match["matched_skill"]

        if required_skill in matched_required_skills:
            continue

        if resume_skill in used_resume_skills:
            continue

        matched_skills.append({
            "required_skill": required_skill,
            "matched_skill": resume_skill,
            "similarity": round(
                match["similarity"] * 100,
                2
            )
        })

        matched_required_skills.add(
            required_skill
        )

        used_resume_skills.add(
            resume_skill
        )

    # -------------------------------------------------
    # Determine missing skills
    # -------------------------------------------------

    missing_skills = [
        skill
        for skill in required_skills
        if skill not in matched_required_skills
    ]

    # -------------------------------------------------
    # Calculate semantic skill score
    # -------------------------------------------------

    total_required = len(
        required_skills
    )

    matched_count = len(
        matched_skills
    )

    if total_required > 0:
        score = (
            matched_count
            / total_required
        ) * 100
    else:
        score = 0.0

    return {
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "semantic_skill_score": round(
            score,
            2
        )
    }

def validate_esco_candidates(candidates, threshold=0.70):
    if not candidates:
        return []

    sbert_model = get_model()

    validated_candidates = []

    for candidate in candidates:

        phrase = candidate["phrase"]
        preferred_label = candidate["preferred_label"]

        embeddings = sbert_model.encode(
            [phrase, preferred_label],
            convert_to_numpy=True
        )

        similarity = cosine_similarity(
            [embeddings[0]],
            [embeddings[1]]
        )[0][0]

        similarity_percentage = round(
            similarity * 100,
            2
        )

        shared_words = set(candidate.get("shared_words", []))

        # Remove very generic words that are not strong
        # evidence of a skill match.
        generic_words = {
            "accounting",
            "records",
            "statements",
            "reporting",
            "expenses",
            "monthly",
            "business"
        }

        meaningful_shared_words = (
            shared_words - generic_words
        )

        has_strong_shared_word = any(
            len(word) >= 5
            for word in meaningful_shared_words
        )

        # Very high semantic similarity can still validate
        # a candidate even without shared words.
        strong_semantic_match = similarity >= 0.85

        valid_match = (
            similarity >= threshold
            and (
                has_strong_shared_word
                or strong_semantic_match
            )
        )

        if valid_match:

            validated_candidates.append({
                **candidate,
                "similarity": similarity_percentage
            })

    validated_candidates.sort(
        key=lambda item: item["similarity"],
        reverse=True
    )

    return validated_candidates

def select_best_esco_candidates(candidates):
    """
    Keep only the strongest ESCO candidate for each
    extracted phrase.
    """

    if not candidates:
        return []

    best_candidates = {}

    for candidate in candidates:

        phrase = candidate["phrase"]

        current = best_candidates.get(phrase)

        if current is None:
            best_candidates[phrase] = candidate
            continue

        if candidate["similarity"] > current["similarity"]:
            best_candidates[phrase] = candidate

    selected = list(best_candidates.values())

    selected.sort(
        key=lambda item: item["similarity"],
        reverse=True
    )

    return selected

def retrieve_semantic_esco_candidates(
    phrases,
    esco_skills,
    top_k=5
):
    """
    Retrieve semantic ESCO candidates using a controlled
    candidate pool.

    Generic words alone are not sufficient for candidate
    generation. Results are deduplicated by ESCO preferred
    label.
    """

    if not phrases or not esco_skills:
        return []

    sbert_model = get_model()

    generic_words = {
        "data",
        "record",
        "records",
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
        "system",
        "systems",
        "process",
        "processes",
        "planning",
        "management",
        "skill",
        "skills",
        "work",
        "working",
        "operation",
        "operations"
    }

    results = []

    for phrase in phrases:

        phrase = phrase.strip().lower()

        if not phrase:
            continue

        phrase_words = set(phrase.split())

        # ---------------------------------------------
        # Identify specific words.
        # ---------------------------------------------

        specific_phrase_words = {
            word
            for word in phrase_words
            if len(word) >= 5
            and word not in generic_words
        }

        # We need at least one specific word.
        if not specific_phrase_words:
            continue

        candidate_pool = []

        for esco_label, skill_data in esco_skills.items():

            esco_label = esco_label.strip().lower()

            if not esco_label:
                continue

            label_words = set(esco_label.split())

            # -----------------------------------------
            # Find shared specific words.
            # -----------------------------------------

            shared_specific_words = (
                specific_phrase_words & label_words
            )

            # -----------------------------------------
            # If there is no useful lexical evidence,
            # don't put the concept into this pool.
            # -----------------------------------------

            if not shared_specific_words:
                continue

            candidate_pool.append(
                (
                    esco_label,
                    skill_data,
                    shared_specific_words
                )
            )

        if not candidate_pool:
            continue

        # ---------------------------------------------
        # Encode phrase once.
        # ---------------------------------------------

        phrase_embedding = sbert_model.encode(
            [phrase],
            convert_to_numpy=True
        )

        candidate_labels = [
            item[0]
            for item in candidate_pool
        ]

        candidate_embeddings = sbert_model.encode(
            candidate_labels,
            convert_to_numpy=True
        )

        similarities = cosine_similarity(
            phrase_embedding,
            candidate_embeddings
        )[0]

        # ---------------------------------------------
        # Deduplicate by preferred ESCO concept.
        # ---------------------------------------------

        best_by_preferred_label = {}

        for (
            candidate_data,
            similarity
        ) in zip(candidate_pool, similarities):

            esco_label, skill_data, shared_words = (
                candidate_data
            )

            preferred_label = (
                skill_data["preferred_label"]
                .strip()
                .lower()
            )

            similarity_score = float(similarity)

            existing = best_by_preferred_label.get(
                preferred_label
            )

            if (
                existing is None
                or similarity_score > existing["similarity"]
            ):
                best_by_preferred_label[
                    preferred_label
                ] = {
                    "phrase": phrase,
                    "preferred_label": (
                        skill_data["preferred_label"]
                    ),
                    "similarity": similarity_score,
                    "shared_words": sorted(
                        shared_words
                    )
                }

        ranked = sorted(
            best_by_preferred_label.values(),
            key=lambda item: item["similarity"],
            reverse=True
        )

        # ---------------------------------------------
        # Keep top candidates for this phrase.
        # ---------------------------------------------

        for candidate in ranked[:top_k]:

            results.append({
                "phrase": candidate["phrase"],
                "preferred_label": candidate[
                    "preferred_label"
                ],
                "similarity": round(
                    candidate["similarity"] * 100,
                    2
                ),
                "shared_words": candidate[
                    "shared_words"
                ]
            })

    return results

def validate_retrieved_esco_candidates(
    candidates,
    threshold=0.70
):
    """
    Validate semantically retrieved ESCO candidates.

    Only candidates with sufficiently strong SBERT
    similarity are retained.
    """

    if not candidates:
        return []

    validated = []

    for candidate in candidates:

        similarity = candidate.get("similarity", 0)

        if similarity >= threshold * 100:

            validated.append({
                **candidate,
                "similarity": round(similarity, 2)
            })

    validated.sort(
        key=lambda item: item["similarity"],
        reverse=True
    )

    return validated

def select_best_retrieved_esco_candidates(candidates):
    """
    Select the strongest ESCO candidate for each phrase.

    Each original phrase is assigned to only one
    ESCO concept: the candidate with the highest
    semantic similarity.
    """

    if not candidates:
        return []

    best_candidates = {}

    for candidate in candidates:

        phrase = candidate["phrase"]
        current = best_candidates.get(phrase)

        if (
            current is None
            or candidate["similarity"] > current["similarity"]
        ):
            best_candidates[phrase] = candidate

    selected = list(best_candidates.values())

    selected.sort(
        key=lambda item: item["similarity"],
        reverse=True
    )

    return selected

def get_semantic_skill_candidates(
    phrases,
    esco_skills,
    threshold=0.70
):
    """
    Find strong ESCO semantic evidence for resume phrases.

    The original resume phrase is preserved as the skill name.
    ESCO is only used as semantic evidence.
    """

    if not phrases:
        return []

    retrieved = retrieve_semantic_esco_candidates(
        phrases,
        esco_skills
    )

    # Use the stricter validation rule.
    validated = validate_esco_candidates(
        retrieved,
        threshold=threshold
    )

    selected = select_best_esco_candidates(
        validated
    )

    results = []

    for candidate in selected:

        phrase = candidate["phrase"].strip().lower()

        if not phrase:
            continue

        results.append({
            "skill": phrase,
            "esco_label": candidate["preferred_label"],
            "similarity": candidate["similarity"],
            "shared_words": candidate["shared_words"]
        })

    return results

def is_good_semantic_skill_phrase(phrase):
    """
    Conservative, domain-independent filter for semantic skill phrases.
    """

    if not phrase:
        return False

    words = phrase.lower().split()

    if len(words) < 2:
        return False

    generic_words = {
        "data",
        "information",
        "report",
        "reports",
        "work",
        "working",
        "business",
        "process",
        "processes",
        "activity",
        "activities",
        "thing",
        "things"
    }

    meaningful_words = [
        word
        for word in words
        if word not in generic_words
        and len(word) >= 5
    ]

    return len(meaningful_words) >= 1

def is_likely_skill_phrase(phrase):
    """
    Conservative, domain-independent check for whether
    a multi-word phrase is likely to represent a skill
    or competency.

    This does not depend on a specific domain such as
    Finance, Marketing, or IT.
    """

    if not phrase:
        return False

    words = phrase.lower().split()

    # Skills are generally represented by 2+ words.
    if len(words) < 2:
        return False

    generic_words = {
        "data",
        "information",
        "report",
        "reports",
        "work",
        "working",
        "business",
        "thing",
        "things",
        "task",
        "tasks",
        "activity",
        "activities"
    }

    # Reject phrases consisting mostly of generic words.
    meaningful_words = [
        word
        for word in words
        if word not in generic_words
        and len(word) >= 4
    ]

    if len(meaningful_words) == 0:
        return False

    return True