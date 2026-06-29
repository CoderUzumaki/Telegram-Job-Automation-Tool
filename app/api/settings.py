from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel

from app.api.deps import verify_credentials

router = APIRouter(prefix="/api/settings", tags=["settings"])


class SettingBody(BaseModel):
    value: dict


def _split_csv(value: str) -> list[str]:
    return [x.strip() for x in value.split(",") if x.strip()]


@router.get("/profile")
async def get_profile(request: Request, user: str = Depends(verify_credentials)):
    s = request.app.state.repo.get_setting("profile")
    return s.value_json if s else {}


@router.put("/profile")
async def put_profile(body: SettingBody, request: Request, user: str = Depends(verify_credentials)):
    s = request.app.state.repo.put_setting("profile", body.value)
    return {"version": s.version}


@router.post("/profile-form")
async def save_profile_form(
    request: Request,
    batch: str = Form(""),
    strict_batch: str = Form(""),
    roles: str = Form(""),
    skills: str = Form(""),
    locations: str = Form(""),
    user: str = Depends(verify_credentials),
):
    existing = request.app.state.repo.get_setting("profile")
    current = existing.value_json if existing else {}
    value = {
        **current,
        "batch": batch.strip(),
        "strict_batch": strict_batch == "on",
        "roles": _split_csv(roles),
        "skills": _split_csv(skills),
        "locations": _split_csv(locations),
    }
    request.app.state.repo.put_setting("profile", value)
    return RedirectResponse("/settings?saved=profile", status_code=303)


@router.get("/filter-rules")
async def get_filter_rules(request: Request, user: str = Depends(verify_credentials)):
    s = request.app.state.repo.get_setting("filter_rules")
    return s.value_json if s else {}


@router.put("/filter-rules")
async def put_filter_rules(body: SettingBody, request: Request, user: str = Depends(verify_credentials)):
    s = request.app.state.repo.put_setting("filter_rules", body.value)
    return {"version": s.version}


@router.post("/filter-rules-form")
async def save_filter_form(
    request: Request,
    include: str = Form(""),
    exclude: str = Form(""),
    user: str = Depends(verify_credentials),
):
    value = {"include": _split_csv(include), "exclude": _split_csv(exclude)}
    request.app.state.repo.put_setting("filter_rules", value)
    return RedirectResponse("/settings?saved=rules", status_code=303)


@router.get("/score-threshold")
async def get_threshold(request: Request, user: str = Depends(verify_credentials)):
    s = request.app.state.repo.get_setting("score_threshold")
    return s.value_json if s else {"value": 65}


@router.put("/score-threshold")
async def put_threshold(body: SettingBody, request: Request, user: str = Depends(verify_credentials)):
    s = request.app.state.repo.put_setting("score_threshold", body.value)
    return {"version": s.version}


@router.post("/score-threshold-form")
async def save_threshold_form(
    request: Request,
    value: int = Form(65),
    user: str = Depends(verify_credentials),
):
    request.app.state.repo.put_setting("score_threshold", {"value": value})
    return RedirectResponse("/settings?saved=threshold", status_code=303)


@router.get("/page", response_class=HTMLResponse)
async def settings_page(request: Request, user: str = Depends(verify_credentials)):
    repo = request.app.state.repo
    profile = repo.get_setting("profile")
    rules = repo.get_setting("filter_rules")
    threshold = repo.get_setting("score_threshold")
    listener = getattr(request.app.state, "listener", None)
    return request.app.state.templates.TemplateResponse(
        request,
        "settings.html",
        {
            "profile": profile.value_json if profile else {},
            "filter_rules": rules.value_json if rules else {},
            "threshold": threshold.value_json.get("value", 65) if threshold else 65,
            "telegram_connected": listener.connected if listener else False,
            "user": user,
            "page": "settings",
            "saved": request.query_params.get("saved"),
        },
    )
