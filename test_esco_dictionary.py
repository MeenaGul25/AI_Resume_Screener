from app.services.esco_loader import build_esco_skill_dictionary

esco_skills = build_esco_skill_dictionary()

print("\n========== DICTIONARY CHECK ==========")

for key in esco_skills:
    if "customer relationship management" in key:
        print("FOUND KEY:")
        print(repr(key))

        print("\nDATA:")
        print(esco_skills[key])

print("======================================")