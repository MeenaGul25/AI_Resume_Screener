from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)
from app import db

from app.models.resume import Resume
from app.models.job_description import JobDescription
from app.models.matching_result import MatchingResult

from app.services.matcher import calculate_match_score

from app.services.candidate_analyzer import (
    analyze_candidate,
    calculate_experience_score,
    calculate_education_score,
    calculate_final_score,
    classify_candidate,
    get_hr_recommendation,
    generate_strengths_weaknesses

)

from app.services.plagiarism_detector import (
    find_most_similar_resume
)

matching_bp = Blueprint(
    "matching",
    __name__
)


@matching_bp.route(
    "/match",
    methods=["GET", "POST"]
)
def match_resume():

    # Make sure HR is logged in
    if "user_id" not in session:
        return redirect(
            url_for("auth.login")
        )

    user_id = session["user_id"]

    # Get this user's resumes
    resumes = Resume.query.filter_by(
        user_id=user_id
    ).all()

    # Get this user's job descriptions
    job_descriptions = JobDescription.query.filter_by(
        user_id=user_id
    ).all()

    if request.method == "POST":

        # Load heavy AI components only when matching is requested.
        from app.services.semantic_matcher import (
            calculate_semantic_match_score
        )

        from app.services.skill_extractor import (
            compare_skills
        )

        resume_id = request.form.get(
            "resume_id"
        )

        job_description_id = request.form.get(
            "job_description_id"
        )

        if not resume_id or not job_description_id:

            flash(
                "Please select both a resume and a job description."
            )

            return redirect(
                url_for("matching.match_resume")
            )

        resume = Resume.query.filter_by(
            id=resume_id,
            user_id=user_id
        ).first()

        job_description = JobDescription.query.filter_by(
            id=job_description_id,
            user_id=user_id
        ).first()

        if not resume or not job_description:

            flash(
                "Invalid resume or job description."
            )

            return redirect(
                url_for("matching.match_resume")
            )
        
        other_resumes = Resume.query.filter(
            Resume.user_id == user_id,
            Resume.id != resume.id,
            Resume.filename != resume.filename
        ).all()
        
        

        plagiarism_result = find_most_similar_resume(
            resume,
            other_resumes
        )

        most_similar_resume = plagiarism_result[
            "most_similar_resume"
        ]

        plagiarism_score = plagiarism_result[
            "similarity_score"
        ]
        plagiarism_classification = plagiarism_result[
            "classification"
        ]

        # Calculate similarity
        # Calculate TF-IDF similarity
        tfidf_score = calculate_match_score(
            resume.extracted_text,
            job_description.extracted_text
        )

        # Calculate SBERT semantic similarity
        semantic_score = calculate_semantic_match_score(
            resume.extracted_text,
            job_description.extracted_text
        )

        

        # Analyze skills
        skill_analysis = compare_skills(
            resume.extracted_text,
            job_description.extracted_text
        )

        skills_score = skill_analysis["skills_score"]

        # Analyze experience and education
        candidate_analysis = analyze_candidate(
            resume.extracted_text,
            job_description.extracted_text
        )

        # Calculate experience score
        experience_score = calculate_experience_score(
            candidate_analysis["experience"]["candidate_years"],
            candidate_analysis["experience"]["required_years"]
        )

        # Calculate education score
        education_score = calculate_education_score(
            candidate_analysis["education"]["candidate_education"],
            candidate_analysis["education"]["required_education"]
        )

        # Calculate final weighted score
        final_score = calculate_final_score(
            semantic_score=semantic_score,
            skills_score=skill_analysis["skills_score"],
            tfidf_score=tfidf_score,
            experience_score=experience_score,
            education_score=education_score
        )
        candidate_classification = classify_candidate(
            final_score
        )

        hr_recommendation = get_hr_recommendation(
            final_score
        )

        strengths_weaknesses = generate_strengths_weaknesses(
            matched_skills=skill_analysis["matched_skills"],
            missing_skills=skill_analysis["missing_skills"],
            experience_analysis=candidate_analysis["experience"],
            education_analysis=candidate_analysis["education"]
        )

        # Save matching result to database
        matching_result = MatchingResult(
            resume_id=resume.id,
            job_description_id=job_description.id,

            tfidf_score=tfidf_score,
            semantic_score=semantic_score,
            skills_score=skill_analysis["skills_score"],
            experience_score=experience_score,
            education_score=education_score,

            final_score=final_score,

            candidate_classification=candidate_classification,
            hr_recommendation=hr_recommendation,

            plagiarism_score=plagiarism_score,
            plagiarism_classification=plagiarism_classification
        )

        db.session.add(matching_result)
        db.session.commit()

        # Display matching result
        return render_template(
            "match_result.html",

            resume=resume,

            job_description=job_description,

            tfidf_score=tfidf_score,

            semantic_score=semantic_score,

            score=final_score,

            candidate_classification=candidate_classification,

            hr_recommendation=hr_recommendation,

            most_similar_resume=most_similar_resume,

            plagiarism_score=plagiarism_score,

            plagiarism_classification=plagiarism_classification,

            strengths=strengths_weaknesses["strengths"],

            weaknesses=strengths_weaknesses["weaknesses"],

            resume_skills=skill_analysis[
                "resume_skills"
            ],

            required_skills=skill_analysis[
                "required_skills"
            ],

            matched_skills=skill_analysis[
                "matched_skills"
            ],

            missing_skills=skill_analysis[
                "missing_skills"
            ],

            semantic_matches=skill_analysis[
                "semantic_matches"
            ],

            skills_score=skill_analysis[
                "skills_score"
            ],

            experience_analysis=candidate_analysis[
                "experience"
            ],

            education_analysis=candidate_analysis[
                "education"
            ],

            experience_score=experience_score,

            education_score=education_score
        )

    return render_template(
        "match.html",
        resumes=resumes,
        job_descriptions=job_descriptions
    )