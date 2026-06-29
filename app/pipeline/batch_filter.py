"""Batch matching for job posts vs user profile."""

import re


def parse_batch_years(batch_value: str | None) -> set[int]:
    if not batch_value:
        return set()
    return {int(y) for y in re.findall(r"20\d{2}", batch_value)}


def batch_matches(user_batch: str | None, job_batch: str | None, strict: bool = True) -> tuple[bool, str]:
    """
    Returns (passed, reason).
    If job has no batch and strict=False, pass. If strict=True, skip when job batch empty.
    """
    if not user_batch:
        return True, ""
    user_years = parse_batch_years(user_batch)
    if not user_years:
        return True, ""
    job_years = parse_batch_years(job_batch)
    if not job_years:
        if strict:
            return False, f"Job has no batch; your batch is {user_batch}"
        return True, ""
    if user_years & job_years:
        return True, ""
    return False, f"Batch mismatch: job targets {job_batch}, your batch is {user_batch}"
