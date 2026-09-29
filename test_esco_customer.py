from app.services.esco_loader import get_esco_skill_variants

skill = "customer relationship management"

variants = get_esco_skill_variants(skill)

print("\n========== ESCO VARIANTS ==========")

if variants:
    for variant in variants:
        print("-", variant)
else:
    print("NO VARIANTS FOUND")

print("===================================")