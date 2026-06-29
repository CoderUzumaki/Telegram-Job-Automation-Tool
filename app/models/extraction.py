from typing import Literal

from pydantic import BaseModel, Field


class ExtractedField(BaseModel):
    value: str | None = None
    source: Literal["parser", "llm", "manual"] | None = None


class Extraction(BaseModel):
    company: ExtractedField = Field(default_factory=ExtractedField)
    role: ExtractedField = Field(default_factory=ExtractedField)
    batch: ExtractedField = Field(default_factory=ExtractedField)
    stipend: ExtractedField = Field(default_factory=ExtractedField)
    location: ExtractedField = Field(default_factory=ExtractedField)
    tags: list[str] = Field(default_factory=list)

    def merge_llm(self, enrichments: dict) -> "Extraction":
        data = self.model_dump()
        for field in ("company", "role", "batch", "stipend", "location"):
            if field in enrichments and enrichments[field]:
                current = data[field]
                if not current.get("value"):
                    data[field] = {"value": str(enrichments[field]), "source": "llm"}
        if enrichments.get("tags"):
            existing = set(data.get("tags") or [])
            for tag in enrichments["tags"]:
                existing.add(str(tag))
            data["tags"] = sorted(existing)
        return Extraction.model_validate(data)
