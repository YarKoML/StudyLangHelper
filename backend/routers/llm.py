"""Роутер настроек LLM (BYOK) и перевода."""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from backend.deps import get_session
from backend.languages import lang_name
from backend.llm import LLMProviderError, list_provider_models, translate_text
from backend.models import Dictionary, LLMSettings, User
from backend.schemas import (
    LLMModelsList,
    LLMModelsRequest,
    LLMSettingsRead,
    LLMSettingsUpdate,
    LLMTranslateRequest,
    LLMTranslateResult,
)
from backend.security import get_current_user

router = APIRouter(prefix="/llm", tags=["llm"])


def _to_read(s: LLMSettings) -> LLMSettingsRead:
    return LLMSettingsRead(base_url=s.base_url, model=s.model, has_key=bool(s.api_key))


@router.get("/settings", response_model=LLMSettingsRead | None)
def get_llm_settings(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    s = session.exec(select(LLMSettings).where(LLMSettings.user_id == current_user.id)).first()
    if not s:
        return None
    return _to_read(s)


@router.put("/settings", response_model=LLMSettingsRead)
def save_llm_settings(
    payload: LLMSettingsUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    s = session.exec(select(LLMSettings).where(LLMSettings.user_id == current_user.id)).first()
    if s:
        s.base_url = payload.base_url
        s.api_key = payload.api_key
        s.model = payload.model
    else:
        s = LLMSettings(
            user_id=current_user.id,
            base_url=payload.base_url,
            api_key=payload.api_key,
            model=payload.model,
        )
    session.add(s)
    session.commit()
    session.refresh(s)
    return _to_read(s)


@router.post("/models", response_model=LLMModelsList)
def list_models(payload: LLMModelsRequest, current_user: User = Depends(get_current_user)):
    try:
        models = list_provider_models(payload.base_url, payload.api_key)
    except LLMProviderError as e:
        raise HTTPException(502, str(e)) from e
    return LLMModelsList(models=models)


@router.post("/translate", response_model=LLMTranslateResult)
def translate(
    payload: LLMTranslateRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    d = session.get(Dictionary, payload.dictionary_id)
    if not d or d.user_id != current_user.id:
        raise HTTPException(404, "Dictionary not found")

    s = session.exec(select(LLMSettings).where(LLMSettings.user_id == current_user.id)).first()
    if not s:
        raise HTTPException(400, "LLM is not configured. Save settings first.")

    target_lang_name = lang_name(d.native_lang, "en")
    try:
        translation = translate_text(payload.text, target_lang_name, s)
    except LLMProviderError as e:
        raise HTTPException(502, str(e)) from e
    return LLMTranslateResult(translation=translation)
