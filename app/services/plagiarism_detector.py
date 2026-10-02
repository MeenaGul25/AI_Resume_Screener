import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def normalize_resume_text(text):
    """
    Normalize resume text before similarity calculation.
    """

    if not text:
        return ""

    # Convert to lowercase
    text = text.lower()

    # Remove punctuation and special characters
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()

def calculate_resume_similarity(
    resume_text_1,
    resume_text_2
):
    """
    Calculate similarity between two resumes
    using TF-IDF and cosine similarity.
    """

    if not resume_text_1 or not resume_text_2:
        return 0.0

    resume_text_1 = normalize_resume_text(
    resume_text_1
    )

    resume_text_2 = normalize_resume_text(
        resume_text_2
    )

    documents = [
        resume_text_1,
        resume_text_2
    ]

    vectorizer = TfidfVectorizer(
        stop_words="english"
    )

    tfidf_matrix = vectorizer.fit_transform(
        documents
    )

    similarity = cosine_similarity(
        tfidf_matrix[0:1],
        tfidf_matrix[1:2]
    )[0][0]

    return round(
        similarity * 100,
        2
    )


def classify_similarity(similarity_score):
    """
    Classify resume similarity based on
    the similarity percentage.
    """

    if similarity_score >= 80:
        return "Very High Similarity"

    elif similarity_score >= 60:
        return "High Similarity"

    elif similarity_score >= 30:
        return "Moderate Similarity"

    else:
        return "Low Similarity"

def find_most_similar_resume(
    current_resume,
    other_resumes
):
    """
    Compare the current resume against
    other stored resumes and return
    the most similar resume.
    """

    highest_similarity = 0.0
    most_similar_resume = None

    for resume in other_resumes:

        if not resume.extracted_text:
            continue

        similarity = calculate_resume_similarity(
            current_resume.extracted_text,
            resume.extracted_text
        )

        print(
            f"PLAGIARISM CHECK: "
            f"{resume.filename} | "
            f"{similarity}%"
        )

        if similarity > highest_similarity:

            highest_similarity = similarity

            most_similar_resume = resume

    return {
        "most_similar_resume": most_similar_resume,
        "similarity_score": highest_similarity,
        "classification": classify_similarity(
            highest_similarity
        )
    }

