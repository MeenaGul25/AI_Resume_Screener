import os
import re

import numpy as np
import torch

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from app.services.esco_loader import (
    get_esco_skill_variants
)


# ---------------------------------------------------------
# Runtime optimization
# ---------------------------------------------------------

# Prevent unnecessary tokenizer parallelism.
os.environ.setdefault(
    "TOKENIZERS_PARALLELISM",
    "false"
)

# Render Free has limited CPU resources.
# Limiting PyTorch threads reduces unnecessary resource usage.
try:
    torch.set_num_threads(1)
except Exception:
    pass


# ---------------------------------------------------------
# SBERT model
# ---------------------------------------------------------

model = None

MODEL_NAME = "all-MiniLM-L6-v2"

# Small batches are safer for low-memory environments.
ENCODE_BATCH_SIZE = 16


def get_model():
    """
    Load the SBERT model only once.

    The model remains cached in memory after the first use.
    """

    global model

    if model is None:

        print("Loading SBERT model...")

        model = SentenceTransformer(
            MODEL_NAME
        )

        print("SBERT model loaded successfully.")

    return model


# ---------------------------------------------------------
# Helper: batch encoding
# ---------------------------------------------------------

def encode_texts(
    texts,
    batch_size=ENCODE_BATCH_SIZE
):
    """
    Encode a list of texts using SBERT in small batches.

    This avoids repeatedly calling the model for individual
    strings and keeps peak memory usage lower.
    """

    if not texts:
        return np.empty(
            (0, 384),
            dtype=np.float32
        )

    sbert_model = get_model()

    return sbert_model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=False,
        convert_to_numpy=True
    )


# ---------------------------------------------------------
# Full resume ↔ job description semantic similarity
# ---------------------------------------------------------

def calculate_semantic_match_score(
    resume_text,
    job_description_text
):

    if not resume_text or not job_description_text:
        return 0.0

    # Encode both texts together instead of making
    # two separate model calls.
    embeddings = encode_texts(
        [
            resume_text,
            job_description_text
        ],
        batch_size=2
    )

    resume_embedding = embeddings[0]
    job_embedding = embeddings[1]

    similarity = cosine_similarity(
        [resume_embedding],
        [job_embedding]
    )[0][0]

    score = similarity * 100

    return round(
        score,
        2
    )


# ---------------------------------------------------------
# Meaningful word extraction
# ---------------------------------------------------------

def get_meaningful_words(text):

    if not text:
        return set()

    stop_words = {
        "a",
        "an",
        "and",
        "the",
        "of",
        "to",
        "in",
        "on",
        "for",
        "with",
        "by",
        "from",
        "at",
        "as",
        "is",
        "are",
        "be",
        "or"
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

        word = plural_map.get(
            word,
            word
        )

        normalized_words.add(
            word
        )

    return normalized_words


# ---------------------------------------------------------
# Skill semantic similarity
# ---------------------------------------------------------

def calculate_skill_semantic_similarity(
    resume_skills,
    required_skills,
    threshold=0.65
):
    """
    Compare resume skills with required skills using SBERT
    and ESCO skill variants.

    Optimized version:
    - Each unique skill variant is encoded only once.
    - Resume and required variants are encoded in batches.
    - The original matching rules are preserved.
    """

    if not resume_skills or not required_skills:

        return {
            "matched_skills": [],
            "missing_skills": list(
                required_skills
            ),
            "semantic_skill_score": 0.0
        }

    resume_skills = list(
        resume_skills
    )

    required_skills = list(
        required_skills
    )

    # -------------------------------------------------
    # Build variant lists
    # -------------------------------------------------

    required_variant_map = {}

    for required_skill in required_skills:

        variants = get_esco_skill_variants(
            required_skill
        )

        if not variants:
            variants = [
                required_skill
            ]

        required_variant_map[
            required_skill
        ] = variants

    resume_variant_map = {}

    for resume_skill in resume_skills:

        variants = get_esco_skill_variants(
            resume_skill
        )

        if not variants:
            variants = [
                resume_skill
            ]

        resume_variant_map[
            resume_skill
        ] = variants

    # -------------------------------------------------
    # Collect unique variants
    # -------------------------------------------------

    all_variants = []

    for variants in required_variant_map.values():
        all_variants.extend(
            variants
        )

    for variants in resume_variant_map.values():
        all_variants.extend(
            variants
        )

    # Remove duplicates while preserving order.
    unique_variants = list(
        dict.fromkeys(
            variant.strip()
            for variant in all_variants
            if variant and variant.strip()
        )
    )

    # -------------------------------------------------
    # Encode EVERY unique variant only once
    # -------------------------------------------------

    embeddings = encode_texts(
        unique_variants
    )

    embedding_map = {
        text: embedding
        for text, embedding
        in zip(
            unique_variants,
            embeddings
        )
    }

    # -------------------------------------------------
    # Generate all possible matches
    # -------------------------------------------------

    possible_matches = []

    for required_skill in required_skills:

        required_variants = (
            required_variant_map[
                required_skill
            ]
        )

        required_embeddings = np.vstack([
            embedding_map[
                variant.strip()
            ]
            for variant
            in required_variants
            if variant.strip()
            in embedding_map
        ])

        required_words = (
            get_meaningful_words(
                required_skill
            )
        )

        for resume_skill in resume_skills:

            resume_variants = (
                resume_variant_map[
                    resume_skill
                ]
            )

            resume_embeddings = np.vstack([
                embedding_map[
                    variant.strip()
                ]
                for variant
                in resume_variants
                if variant.strip()
                in embedding_map
            ])

            # Compare all variants and keep the strongest
            # semantic relationship.
            similarity_matrix = cosine_similarity(
                required_embeddings,
                resume_embeddings
            )

            raw_similarity = float(
                similarity_matrix.max()
            )

            resume_words = (
                get_meaningful_words(
                    resume_skill
                )
            )

            lexical_overlap = (
                required_words
                & resume_words
            )

            has_lexical_evidence = (
                len(lexical_overlap) >= 1
                and any(
                    len(word) >= 8
                    for word
                    in lexical_overlap
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
                    "required_skill":
                        required_skill,

                    "matched_skill":
                        resume_skill,

                    "similarity":
                        raw_similarity,

                    "lexical":
                        has_lexical_evidence
                })

    # -------------------------------------------------
    # Sort by strongest similarity
    # -------------------------------------------------

    possible_matches.sort(
        key=lambda match:
            match["similarity"],
        reverse=True
    )

    # -------------------------------------------------
    # Assign each resume skill only once
    # -------------------------------------------------

    matched_skills = []

    matched_required_skills = set()

    used_resume_skills = set()

    for match in possible_matches:

        required_skill = (
            match["required_skill"]
        )

        resume_skill = (
            match["matched_skill"]
        )

        if required_skill in (
            matched_required_skills
        ):
            continue

        if resume_skill in (
            used_resume_skills
        ):
            continue

        matched_skills.append({
            "required_skill":
                required_skill,

            "matched_skill":
                resume_skill,

            "similarity":
                round(
                    match["similarity"]
                    * 100,
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
        if skill
        not in matched_required_skills
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
        "matched_skills":
            matched_skills,

        "missing_skills":
            missing_skills,

        "semantic_skill_score":
            round(
                score,
                2
            )
    }


# ---------------------------------------------------------
# Validate ESCO semantic candidates
# ---------------------------------------------------------

def validate_esco_candidates(
    candidates,
    threshold=0.70
):

    if not candidates:
        return []

    # -------------------------------------------------
    # Encode all phrase/label pairs in batches
    # instead of calling SBERT for every candidate.
    # -------------------------------------------------

    pair_texts = []

    for candidate in candidates:

        pair_texts.append(
            candidate["phrase"]
        )

        pair_texts.append(
            candidate["preferred_label"]
        )

    embeddings = encode_texts(
        pair_texts
    )

    validated_candidates = []

    for index, candidate in enumerate(
        candidates
    ):

        phrase_embedding = (
            embeddings[index * 2]
        )

        label_embedding = (
            embeddings[index * 2 + 1]
        )

        similarity = cosine_similarity(
            [phrase_embedding],
            [label_embedding]
        )[0][0]

        similarity_percentage = round(
            similarity * 100,
            2
        )

        shared_words = set(
            candidate.get(
                "shared_words",
                []
            )
        )

        # Remove generic words that are weak
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
            shared_words
            - generic_words
        )

        has_strong_shared_word = any(
            len(word) >= 5
            for word
            in meaningful_shared_words
        )

        strong_semantic_match = (
            similarity >= 0.85
        )

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

                "similarity":
                    similarity_percentage
            })

    validated_candidates.sort(
        key=lambda item:
            item["similarity"],
        reverse=True
    )

    return validated_candidates


# ---------------------------------------------------------
# Select best ESCO candidate
# ---------------------------------------------------------

def select_best_esco_candidates(
    candidates
):
    """
    Keep only the strongest ESCO candidate
    for each extracted phrase.
    """

    if not candidates:
        return []

    best_candidates = {}

    for candidate in candidates:

        phrase = candidate[
            "phrase"
        ]

        current = best_candidates.get(
            phrase
        )

        if current is None:

            best_candidates[
                phrase
            ] = candidate

            continue

        if (
            candidate["similarity"]
            >
            current["similarity"]
        ):

            best_candidates[
                phrase
            ] = candidate

    selected = list(
        best_candidates.values()
    )

    selected.sort(
        key=lambda item:
            item["similarity"],
        reverse=True
    )

    return selected


# ---------------------------------------------------------
# Retrieve semantic ESCO candidates
# ---------------------------------------------------------

def retrieve_semantic_esco_candidates(
    phrases,
    esco_skills,
    top_k=5
):
    """
    Retrieve semantic ESCO candidates using
    a controlled candidate pool.

    Generic words alone are not sufficient for
    candidate generation.

    ESCO labels are encoded in batches and cached
    within this function so that the same label
    is not encoded repeatedly.
    """

    if not phrases or not esco_skills:
        return []

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

    # -------------------------------------------------
    # Local embedding cache.
    #
    # This prevents the same ESCO label from being
    # encoded again for different phrases.
    # -------------------------------------------------

    label_embedding_cache = {}

    for phrase in phrases:

        phrase = (
            phrase
            .strip()
            .lower()
        )

        if not phrase:
            continue

        phrase_words = set(
            phrase.split()
        )

        specific_phrase_words = {
            word
            for word
            in phrase_words
            if len(word) >= 5
            and word not in generic_words
        }

        if not specific_phrase_words:
            continue

        candidate_pool = []

        # -------------------------------------------------
        # Build lexical candidate pool
        # -------------------------------------------------

        for esco_label, skill_data in (
            esco_skills.items()
        ):

            esco_label = (
                esco_label
                .strip()
                .lower()
            )

            if not esco_label:
                continue

            label_words = set(
                esco_label.split()
            )

            shared_specific_words = (
                specific_phrase_words
                & label_words
            )

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

        # -------------------------------------------------
        # Encode phrase once
        # -------------------------------------------------

        phrase_embedding = encode_texts(
            [phrase],
            batch_size=1
        )[0]

        # -------------------------------------------------
        # Encode only labels that are not cached
        # -------------------------------------------------

        missing_labels = []

        for item in candidate_pool:

            label = item[0]

            if label not in (
                label_embedding_cache
            ):

                missing_labels.append(
                    label
                )

        if missing_labels:

            missing_embeddings = encode_texts(
                missing_labels
            )

            for label, embedding in zip(
                missing_labels,
                missing_embeddings
            ):

                label_embedding_cache[
                    label
                ] = embedding

        # -------------------------------------------------
        # Compare phrase against candidate labels
        # -------------------------------------------------

        candidate_labels = [
            item[0]
            for item in candidate_pool
        ]

        candidate_embeddings = np.vstack([
            label_embedding_cache[
                label
            ]
            for label
            in candidate_labels
        ])

        similarities = cosine_similarity(
            [phrase_embedding],
            candidate_embeddings
        )[0]

        # -------------------------------------------------
        # Deduplicate by preferred ESCO concept
        # -------------------------------------------------

        best_by_preferred_label = {}

        for (
            candidate_data,
            similarity
        ) in zip(
            candidate_pool,
            similarities
        ):

            (
                esco_label,
                skill_data,
                shared_words
            ) = candidate_data

            preferred_label = (
                skill_data[
                    "preferred_label"
                ]
                .strip()
                .lower()
            )

            similarity_score = float(
                similarity
            )

            existing = (
                best_by_preferred_label.get(
                    preferred_label
                )
            )

            if (
                existing is None
                or similarity_score
                >
                existing["similarity"]
            ):

                best_by_preferred_label[
                    preferred_label
                ] = {

                    "phrase":
                        phrase,

                    "preferred_label":
                        skill_data[
                            "preferred_label"
                        ],

                    "similarity":
                        similarity_score,

                    "shared_words":
                        sorted(
                            shared_words
                        )
                }

        ranked = sorted(
            best_by_preferred_label.values(),
            key=lambda item:
                item["similarity"],
            reverse=True
        )

        # -------------------------------------------------
        # Keep top candidates
        # -------------------------------------------------

        for candidate in ranked[
            :top_k
        ]:

            results.append({

                "phrase":
                    candidate["phrase"],

                "preferred_label":
                    candidate[
                        "preferred_label"
                    ],

                "similarity":
                    round(
                        candidate[
                            "similarity"
                        ] * 100,
                        2
                    ),

                "shared_words":
                    candidate[
                        "shared_words"
                    ]
            })

    return results


# ---------------------------------------------------------
# Older helper retained for compatibility
# ---------------------------------------------------------

def validate_retrieved_esco_candidates(
    candidates,
    threshold=0.70
):
    """
    Validate retrieved ESCO candidates using
    their already-calculated similarity.
    """

    if not candidates:
        return []

    validated = []

    for candidate in candidates:

        similarity = candidate.get(
            "similarity",
            0
        )

        if similarity >= (
            threshold * 100
        ):

            validated.append({
                **candidate,

                "similarity":
                    round(
                        similarity,
                        2
                    )
            })

    validated.sort(
        key=lambda item:
            item["similarity"],
        reverse=True
    )

    return validated


# ---------------------------------------------------------
# Older helper retained for compatibility
# ---------------------------------------------------------

def select_best_retrieved_esco_candidates(
    candidates
):
    """
    Select the strongest ESCO candidate
    for each phrase.
    """

    if not candidates:
        return []

    best_candidates = {}

    for candidate in candidates:

        phrase = candidate[
            "phrase"
        ]

        current = best_candidates.get(
            phrase
        )

        if (
            current is None
            or candidate["similarity"]
            >
            current["similarity"]
        ):

            best_candidates[
                phrase
            ] = candidate

    selected = list(
        best_candidates.values()
    )

    selected.sort(
        key=lambda item:
            item["similarity"],
        reverse=True
    )

    return selected


# ---------------------------------------------------------
# Main semantic ESCO skill candidate function
# ---------------------------------------------------------

def get_semantic_skill_candidates(
    phrases,
    esco_skills,
    threshold=0.70
):
    """
    Find strong ESCO semantic evidence
    for resume phrases.

    The original resume phrase is preserved
    as the skill name.

    ESCO is only used as semantic evidence.
    """

    if not phrases:
        return []

    retrieved = (
        retrieve_semantic_esco_candidates(
            phrases,
            esco_skills
        )
    )

    validated = (
        validate_esco_candidates(
            retrieved,
            threshold=threshold
        )
    )

    selected = (
        select_best_esco_candidates(
            validated
        )
    )

    results = []

    for candidate in selected:

        phrase = (
            candidate["phrase"]
            .strip()
            .lower()
        )

        if not phrase:
            continue

        results.append({

            "skill":
                phrase,

            "esco_label":
                candidate[
                    "preferred_label"
                ],

            "similarity":
                candidate[
                    "similarity"
                ],

            "shared_words":
                candidate[
                    "shared_words"
                ]
        })

    return results


# ---------------------------------------------------------
# Semantic skill phrase validation
# ---------------------------------------------------------

def is_good_semantic_skill_phrase(
    phrase
):
    """
    Conservative, domain-independent filter
    for semantic skill phrases.
    """

    if not phrase:
        return False

    words = (
        phrase
        .lower()
        .split()
    )

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

    return (
        len(meaningful_words) >= 1
    )


# ---------------------------------------------------------
# Likely skill phrase validation
# ---------------------------------------------------------

def is_likely_skill_phrase(
    phrase
):
    """
    Conservative, domain-independent check
    for whether a multi-word phrase is likely
    to represent a skill or competency.
    """

    if not phrase:
        return False

    words = (
        phrase
        .lower()
        .split()
    )

    # Skills are generally represented
    # by two or more words.
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

    meaningful_words = [
        word
        for word in words
        if word not in generic_words
        and len(word) >= 4
    ]

    if len(meaningful_words) == 0:
        return False

    return True