from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.api.deps import verify_credentials
from app.config import settings
from app.export.csv_export import export_message

router = APIRouter(tags=["messages"])


def _render_inbox_action_response(request: Request, acted_id: int, prior_ids: list[int]) -> HTMLResponse:
    repo = request.app.state.repo
    messages = repo.get_inbox(limit=500)
    selected = repo.resolve_post_action_selection(acted_id, prior_ids)
    return request.app.state.templates.TemplateResponse(
        request,
        "partials/inbox_action_response.html",
        {
            "messages": messages,
            "selected": selected,
            "inbox_count": len(messages),
        },
    )


@router.get("/api/messages/{message_id}")
async def get_message(message_id: int, request: Request, user: str = Depends(verify_credentials)):
    msg = request.app.state.repo.get_by_id(message_id)
    if not msg:
        raise HTTPException(404, "Message not found")
    read_only = request.query_params.get("readonly") == "1"
    if request.headers.get("HX-Request"):
        template = "partials/job_detail_readonly.html" if read_only else "partials/job_detail.html"
        return request.app.state.templates.TemplateResponse(
            request,
            template,
            {"message": msg},
        )
    return msg.model_dump(mode="json")


@router.post("/api/messages/{message_id}/approve")
async def approve_message(message_id: int, request: Request, user: str = Depends(verify_credentials)):
    repo = request.app.state.repo
    prior_ids = [m.id for m in repo.get_inbox(limit=500)]
    msg = repo.approve(message_id)
    if not msg:
        raise HTTPException(404, "Message not found or not approvable")
    msg = repo.get_by_id(message_id)
    try:
        await export_message(msg, repo, settings.csv_export_path, settings.google_sheet_id)
    except Exception as exc:
        repo.mark_export_failed(message_id, str(exc))
    if request.headers.get("HX-Request"):
        return _render_inbox_action_response(request, message_id, prior_ids)
    return {"ok": True}


@router.post("/api/messages/{message_id}/reject")
async def reject_message(message_id: int, request: Request, user: str = Depends(verify_credentials)):
    repo = request.app.state.repo
    prior_ids = [m.id for m in repo.get_inbox(limit=500)]
    msg = repo.reject(message_id)
    if not msg:
        raise HTTPException(404, "Message not found")
    if request.headers.get("HX-Request"):
        return _render_inbox_action_response(request, message_id, prior_ids)
    return {"ok": True}


@router.post("/api/messages/{message_id}/retry")
async def retry_processing(message_id: int, request: Request, user: str = Depends(verify_credentials)):
    repo = request.app.state.repo
    repo.reset_processing_for_retry(message_id)
    await request.app.state.queue.enqueue(message_id)
    return {"ok": True}


@router.post("/api/exports/{message_id}/retry")
async def retry_export(message_id: int, request: Request, user: str = Depends(verify_credentials)):
    repo = request.app.state.repo
    msg = repo.get_by_id(message_id)
    if not msg:
        raise HTTPException(404, "Message not found")
    repo.mark_export_pending(message_id)
    await export_message(msg, repo, settings.csv_export_path, settings.google_sheet_id)
    return {"ok": True}
