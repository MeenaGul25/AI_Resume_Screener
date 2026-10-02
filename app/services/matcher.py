from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def calculate_match_score(resume_text, job_description_text):
    """
    Calculate similarity between a resume and a job description
    using TF-IDF and cosine similarity.
    """

    # Make sure both inputs contain text
    if not resume_text or not job_description_text:
        return 0.0

    # Create TF-IDF vectors
    vectorizer = TfidfVectorizer(
        stop_words="english"
    )

    tfidf_matrix = vectorizer.fit_transform(
        [
            resume_text,
            job_description_text
        ]
    )

    # Calculate cosine similarity
    similarity = cosine_similarity(
        tfidf_matrix[0:1],
        tfidf_matrix[1:2]
    )[0][0]

    # Convert to percentage
    score = similarity * 100

    return round(score, 2)

 