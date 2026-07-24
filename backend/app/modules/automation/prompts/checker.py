from pydantic import BaseModel
from typing import List, Literal

class CheckerResultSchema(BaseModel):
    status: Literal["approved", "rejected", "approved_with_fixes"]
    score: int
    issues: List[str]
    auto_fixes: str
    block_reason: str

CHECKER_SYSTEM = """
You are a Checker Agent. Review the content before publication.
Be strict about brand tone and forbidden topics, but do not over-block.
Check for spelling, length, CTA, and legal risks.
"""

CHECKER_USER = """
Content: {content}
Tone required: {tone}
Forbidden topics: {forbidden}
Platform rules: {rules}

Analyze the content and return the verdict.
"""
