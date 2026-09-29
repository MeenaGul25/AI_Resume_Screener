from app.services.semantic_matcher import get_model
from sklearn.metrics.pairwise import cosine_similarity

model = get_model()

resume_skill = "communication"
required_skill = "communicate with customers"

resume_embedding = model.encode(
    [resume_skill],
    convert_to_numpy=True
)

required_embedding = model.encode(
    [required_skill],
    convert_to_numpy=True
)

similarity = cosine_similarity(
    required_embedding,
    resume_embedding
)[0][0]

print("\n========== COMMUNICATION TEST ==========")
print(
    resume_skill,
    "->",
    required_skill
)
print("Similarity:", round(similarity * 100, 2))
print("========================================")