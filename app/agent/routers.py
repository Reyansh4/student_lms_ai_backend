# app/agent/routers.py

import logging
from typing import Any, Dict, Optional, List
from uuid import UUID

from fastapi import (
    APIRouter,
    HTTPException,
    Depends,
    status,
    Request,
)
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session, joinedload
from rapidfuzz import fuzz

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.activity import Activity
from app.schemas.agent import AgentInput, AgentOutput
from app.schemas.activity import (
    ExtendedStartActivityInput,
    ExtendedStartActivityResponse,
)
from app.agent.chat import run_agent

logger = logging.getLogger(__name__)
router = APIRouter()

# this will pull the JWT from Authorization: Bearer <token>
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


@router.post("/agent/chat", response_model=AgentOutput)
async def agent_chat(
    input: AgentInput,
    request: Request,
    token: str = Depends(oauth2_scheme),
):
    # ---- Logging incoming request ----
    logger.info("=== /agent/chat called ===")
    logger.info("Request headers: %s", dict(request.headers))
    body_bytes = await request.body()
    logger.info("Raw body: %s", body_bytes.decode("utf-8"))
    logger.info("Extracted token: %s", token)

    try:
        # merge the token into the details so downstream tools can use it
        payload = input.model_dump()
        payload.setdefault("details", {})["token"] = token

        # run through your LangGraph-based agent
        response = await run_agent(payload)
        logger.info("run_agent response: %s", response)

        return AgentOutput(**response)
    except Exception as e:
        logger.exception("agent_chat failure")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/start-activity",
    response_model=ExtendedStartActivityResponse,
    status_code=status.HTTP_200_OK,
    summary="Start activity by ID or fuzzy-match by details",
)
def start_activity_extended(
    payload: ExtendedStartActivityInput,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # ---- Logging incoming request ----
    logger.info("=== /agent/start-activity called ===")
    logger.info("Request headers: %s", dict(request.headers))
    logger.info("Parsed payload: %r", payload)

    # 1) Direct fetch by ID
    if payload.activity_id:
        logger.info(
            "User %s fetching activity by ID: %s",
            current_user.email,
            payload.activity_id,
        )
        activity = (
            db.query(Activity)
            .options(
                joinedload(Activity.category),
                joinedload(Activity.sub_category),
            )
            .filter(Activity.id == payload.activity_id)
            .first()
        )
        if not activity:
            logger.warning("Activity not found: %s", payload.activity_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity not found",
            )
        return ExtendedStartActivityResponse(
            status="started",
            final_description=activity.final_description,
            suggestions=None,
        )

    # 2) Fuzzy-match fallback
    if not any(
        [payload.activity_name, payload.category_name, payload.subcategory_name]
    ):
        logger.warning("No match fields provided in payload")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide either activity_id or at least one field to fuzzy-match",
        )

    logger.info(
        "User %s fuzzy-matching activity: name=%r, category=%r, subcategory=%r",
        current_user.email,
        payload.activity_name,
        payload.category_name,
        payload.subcategory_name,
    )

    activities = (
        db.query(Activity)
        .options(
            joinedload(Activity.category),
            joinedload(Activity.sub_category),
        )
        .filter(Activity.is_active == True)
        .all()
    )

    candidates: List[Dict[str, Any]] = []
    for act in activities:
        score_name = fuzz.token_set_ratio(
            payload.activity_name or "", act.name or ""
        )
        score_cat = fuzz.token_set_ratio(
            payload.category_name or "", act.category.name or ""
        )
        score_sub = fuzz.token_set_ratio(
            payload.subcategory_name or "", act.sub_category.name or ""
        )
        combined = max(score_name, score_cat, score_sub)

        candidates.append(
            {
                "activity_id": act.id,
                "name": act.name,
                "final_description": act.final_description,
                "score": combined,
                "category_name": act.category.name if act.category else None,
                "subcategory_name": act.sub_category.name
                if act.sub_category
                else None,
            }
        )

    # return top-5 sorted by score
    topk = sorted(candidates, key=lambda x: x["score"], reverse=True)[:5]
    logger.debug("Fuzzy match top-k: %r", topk)

    return ExtendedStartActivityResponse(
        status="matched", final_description=None, suggestions=topk
    )
