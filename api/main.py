from pathlib import Path
from datetime import datetime, timezone
import logging

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv
from sqlalchemy.orm import Session

# Wymuszenie załadowania .env zarówno z katalogu głównego, jak i api/
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)
load_dotenv()  # Fallback na bieżący katalog

# Konfiguracja logowania (TODO z szablonu)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("learningsteps")

from routers.journal_router import router as journal_router
from models.journal_entry import JournalEntry, JournalEntryResponse, JournalEntryUpdate
from repositories.postgres_repository import get_db

app = FastAPI(
    title="LearningSteps API",
    description="A simple learning journal API for tracking daily work, struggles, and intentions"
)
app.include_router(journal_router)


@app.on_event("startup")
async def startup_event():
    logger.info("LearningSteps API started successfully.")


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")


@app.get("/entries/{entry_id}", response_model=JournalEntryResponse)
async def get_entry(entry_id: str, db: Session = Depends(get_db)):
    """Fetch an entry by ID or return a 404 HTTP error."""
    entry = db.query(JournalEntry).filter(JournalEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entry with id '{entry_id}' not found"
        )
    return entry


@app.patch("/entries/{entry_id}", response_model=JournalEntryResponse)
async def update_entry(entry_id: str, entry_update: JournalEntryUpdate, db: Session = Depends(get_db)):
    """Update fields of an existing entry and refresh timestamp."""
    entry = db.query(JournalEntry).filter(JournalEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entry with id '{entry_id}' not found"
        )

    update_data = entry_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(entry, field, value)

    entry.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(entry)
    return entry


@app.delete("/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entry(entry_id: str, db: Session = Depends(get_db)):
    """Delete an entry by ID or return a 404 HTTP error."""
    entry = db.query(JournalEntry).filter(JournalEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entry with id '{entry_id}' not found"
        )

    db.delete(entry)
    db.commit()
    return None