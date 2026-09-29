import csv
from pathlib import Path
from functools import lru_cache

# Location of the ESCO dataset
ESCO_FOLDER = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "esco"
)

@lru_cache(maxsize=1)
def load_esco_skills():
    """
    Load skills from the ESCO skills CSV file.
    """

    file_path = ESCO_FOLDER / "skills_en.csv"

    skills = []

    with open(file_path, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            skills.append({
                "uri": row.get("conceptUri", ""),
                "preferred_label": row.get("preferredLabel", ""),
                "alt_labels": row.get("altLabels", ""),
                "description": row.get("description", ""),
                "skill_type": row.get("skillType", "")
            })

    return skills


def load_esco_occupations():
    """
    Load occupations from the ESCO occupations CSV file.
    """

    file_path = ESCO_FOLDER / "occupations_en.csv"

    occupations = []

    with open(file_path, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            occupations.append({
                "uri": row.get("conceptUri", ""),
                "preferred_label": row.get("preferredLabel", ""),
                "alt_labels": row.get("altLabels", ""),
                "description": row.get("description", ""),
                "definition": row.get("definition", "")
            })

    return occupations


def load_esco_skill_relations():
    """
    Load occupation-skill relationships from ESCO.
    """

    file_path = ESCO_FOLDER / "occupationSkillRelations_en.csv"

    relations = []

    with open(file_path, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            relations.append({
                "occupation_uri": row.get("occupationUri", ""),
                "occupation_label": row.get("occupationLabel", ""),
                "skill_uri": row.get("skillUri", ""),
                "skill_label": row.get("skillLabel", ""),
                "relation_type": row.get("relationType", ""),
                "skill_type": row.get("skillType", "")
            })

    return relations

def build_esco_skill_dictionary():
    skills = load_esco_skills()

    skill_dictionary = {}

    for skill in skills:
        preferred_label = skill["preferred_label"].strip().lower()

        # Add preferred label
        if preferred_label:
            skill_dictionary[preferred_label] = skill

        # Add alternative labels
        alt_labels = skill["alt_labels"]

        if alt_labels:
            alternatives = alt_labels.split("\n")

            for alternative in alternatives:
                alternative = alternative.strip().lower()

                # Ignore extremely short labels
                # to prevent meaningless fragments
                if len(alternative) < 3:
                    continue

                skill_dictionary[alternative] = skill

    return skill_dictionary


def get_esco_skill_variants(skill_name):
    """
    Return the preferred label and alternative labels
    associated with an ESCO skill.

    This allows semantic matching to compare different
    wording variations of the same skill.
    """

    skills = load_esco_skills()

    skill_name = skill_name.strip().lower()

    variants = set()

    for skill in skills:

        preferred_label = (
            skill["preferred_label"]
            .strip()
            .lower()
        )

        alt_labels = skill["alt_labels"]

        labels = [preferred_label]

        if alt_labels:
            labels.extend(
                alternative.strip().lower()
                for alternative in alt_labels.split("\n")
                if alternative.strip()
            )

        if skill_name in labels:

            variants.update(labels)

            break

    return sorted(variants)

##testing

if __name__ == "__main__":
    skills = load_esco_skills()
    occupations = load_esco_occupations()
    relations = load_esco_skill_relations()

    skill_dictionary = build_esco_skill_dictionary()

    print("ESCO DATASET TEST")
    print("-----------------")

    print("Skills:", len(skills))
    print("Occupations:", len(occupations))
    print("Occupation-Skill Relations:", len(relations))
    print("Searchable Skill Terms:", len(skill_dictionary))

    print("\nExample skill terms:")

    for index, term in enumerate(skill_dictionary.keys()):
        print("-", term)

        if index >= 9:
            break