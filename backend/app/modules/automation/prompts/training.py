from pydantic import BaseModel, Field

TRAINING_SYSTEM = """You are the Training Agent for an AI Social Media Manager.
Your job is to analyze human feedback (rejections, manual edits) on generated posts and update the brand's Tone of Voice and preference model.
You will receive the original post, the human's feedback or corrections, and the current Tone of Voice rules.
Your output must be a JSON object containing the updated Tone of Voice rules and any new forbidden topics."""

TRAINING_USER = """
Original Post:
{original_post}

Human Feedback / Edits:
{feedback}

Current Tone of Voice:
{current_tone}

Analyze the feedback. What did the AI do wrong? Update the rules to prevent this in the future.
"""

class TrainingResultSchema(BaseModel):
    analysis: str = Field(..., description="Explanation of what was wrong and what is being changed.")
    updated_tone_rules: list[str] = Field(..., description="A list of updated tone of voice guidelines.")
    new_forbidden_topics: list[str] = Field(..., description="Any new topics to avoid based on this feedback.")
