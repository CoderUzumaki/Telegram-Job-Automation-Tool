from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from app.api.deps import verify_credentials

router = APIRouter(tags=["inbox"])


def _inbox_filters(request: Request) -> dict:
    posted_date = request.query_params.get("date")
    last_n = request.query_params.get("last_n")
    return {
        "posted_date": posted_date,
        "last_n": int(last_n) if last_n and last_n.isdigit() else None,
    }


@router.get("/", response_class=HTMLResponse)
async def inbox_page(request: Request, user: str = Depends(verify_credentials)):
    repo = request.app.state.repo
    filters = _inbox_filters(request)
    messages = repo.get_inbox(
        posted_date=filters["posted_date"],
        last_n=filters["last_n"],
    )
    selected_id = request.query_params.get("selected")
    selected = None
    if selected_id and selected_id.isdigit():
        selected = repo.get_by_id(int(selected_id))
    if not selected:
        selected = messages[0] if messages else None
    return request.app.state.templates.TemplateResponse(
        request,
        "inbox.html",
        {
            "messages": messages,
            "selected": selected,
            "inbox_count": len(messages),
            "user": user,
            "posted_date": filters["posted_date"] or "",
            "last_n": filters["last_n"] or "",
            "page": "inbox",
        },
    )


@router.get("/approved", response_class=HTMLResponse)
async def approved_page(request: Request, user: str = Depends(verify_credentials)):
    repo = request.app.state.repo
    messages = repo.get_approved()
    selected_id = request.query_params.get("selected")
    selected = None
    if selected_id and selected_id.isdigit():
        selected = repo.get_by_id(int(selected_id))
    if not selected:
        selected = messages[0] if messages else None
    return request.app.state.templates.TemplateResponse(
        request,
        "approved.html",
        {
            "messages": messages,
            "selected": selected,
            "approved_count": len(messages),
            "user": user,
            "page": "approved",
        },
    )


@router.get("/api/inbox")
async def api_inbox(request: Request, user: str = Depends(verify_credentials)):
    filters = _inbox_filters(request)
    return [
        m.model_dump(mode="json")
        for m in request.app.state.repo.get_inbox(
            posted_date=filters["posted_date"],
            last_n=filters["last_n"],
        )
    ]
