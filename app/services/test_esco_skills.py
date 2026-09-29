from app.services.skill_extractor import compare_skills


def test_field(field_name, resume_text, job_description):
    print("\n" + "=" * 60)
    print(field_name)
    print("=" * 60)

    result = compare_skills(
        resume_text,
        job_description
    )

    print("\nResume Skills:")
    for skill in result["resume_skills"]:
        print("-", skill)

    print("\nRequired Skills:")
    for skill in result["required_skills"]:
        print("-", skill)

    print("\nMatched Skills:")
    for skill in result["matched_skills"]:
        print("-", skill)

    print("\nMissing Skills:")
    for skill in result["missing_skills"]:
        print("-", skill)

    print("\nSkills Score:")
    print(result["skills_score"])


if __name__ == "__main__":

    # -------------------------------------------------
    # TEST 1: SOFTWARE / IT
    # -------------------------------------------------

    software_resume = """
    Software developer with experience in Python,
    software development, data analysis, project management,
    databases and web development.
    """

    software_job = """
    We are looking for a software developer with experience
    in Python, software development, data analysis and
    project management.
    """

    test_field(
        "TEST 1 - SOFTWARE / IT",
        software_resume,
        software_job
    )


    # -------------------------------------------------
    # TEST 2: ACCOUNTING / FINANCE
    # -------------------------------------------------

    accounting_resume = """
    Experienced accountant with knowledge of financial
    reporting, bookkeeping, accounting, Microsoft Excel,
    financial analysis and preparing financial statements.
    """

    accounting_job = """
    We require an accountant with experience in accounting,
    financial reporting, bookkeeping and financial analysis.
    The candidate should also be able to prepare financial
    statements.
    """

    test_field(
        "TEST 2 - ACCOUNTING / FINANCE",
        accounting_resume,
        accounting_job
    )


    # -------------------------------------------------
    # TEST 3: MARKETING / HR
    # -------------------------------------------------

    marketing_resume = """
    Marketing professional experienced in digital marketing,
    marketing strategy, customer service, communication,
    social media marketing and project management.
    """

    marketing_job = """
    We are looking for a marketing professional with
    experience in digital marketing, marketing strategy,
    customer service and communication.
    """

    test_field(
        "TEST 3 - MARKETING / HR",
        marketing_resume,
        marketing_job
    )