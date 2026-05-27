"""
Entity extraction module for named entity recognition.

Provides regex-based entity extraction with optional LLM enhancement
for extracting structured entities from unstructured text.
"""

import re
import uuid
from typing import Optional

from src.core.types import KnowledgeGraphNode
from src.core.logger import get_logger
from src.services.llm_service import LLMService

logger = get_logger(__name__)


class EntityExtractor:
    """
    Extract named entities from text using regex patterns and optional LLM.

    Supports common entity types such as PERSON, ORG, LOCATION, EMAIL, URL,
    DATE, MONEY, and PERCENT via regex heuristics. When an LLM service is
    provided, it is used for higher-quality extraction with regex serving
    as a fallback.
    """

    # Regex patterns for concrete entity types
    PATTERNS = {
        "EMAIL": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "URL": r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*",
        "PHONE": r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
        "DATE": (
            r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}"
            r"|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s*\d{4})\b"
        ),
        "MONEY": r"\$\d+(?:,\d{3})*(?:\.\d{2})?",
        "PERCENT": r"\d+(?:\.\d+)?%",
    }

    # Heuristic pattern for capitalized phrases (potential persons, orgs, locations)
    CAPITALIZED_PATTERN = r"\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,2})\b"

    def __init__(self, llm_service: Optional[LLMService] = None):
        """
        Initialize the entity extractor.

        Args:
            llm_service: Optional LLM service for advanced entity extraction.
        """
        self.llm_service = llm_service
        self.logger = get_logger(self.__class__.__name__)

    async def extract_entities(self, text: str) -> list[KnowledgeGraphNode]:
        """
        Extract named entities from the given text.

        Entities are first extracted via regex heuristics. If an LLM service
        is configured, it is also consulted and the results are merged.
        Duplicates are removed based on a case-insensitive (label, type) key.

        Args:
            text: Input text to analyze.

        Returns:
            A list of unique extracted entities as ``KnowledgeGraphNode`` instances.
        """
        try:
            entities: list[KnowledgeGraphNode] = []

            # Attempt LLM-based extraction when available
            if self.llm_service is not None:
                try:
                    llm_entities = await self._extract_with_llm(text)
                    if llm_entities:
                        entities.extend(llm_entities)
                except Exception as exc:
                    self.logger.warning(
                        f"LLM entity extraction failed, falling back to regex: {exc}"
                    )

            # Regex-based extraction (fallback / augmentation)
            regex_entities = self._extract_with_regex(text)
            entities.extend(regex_entities)

            # Deduplicate by (label_lower, node_type)
            seen: set[tuple[str, str]] = set()
            unique_entities: list[KnowledgeGraphNode] = []
            for entity in entities:
                key = (entity.label.lower(), entity.node_type)
                if key not in seen:
                    seen.add(key)
                    unique_entities.append(entity)

            self.logger.info(f"Extracted {len(unique_entities)} unique entities")
            return unique_entities

        except Exception as exc:
            self.logger.error(f"Entity extraction failed: {exc}")
            return []

    def _extract_with_regex(self, text: str) -> list[KnowledgeGraphNode]:
        """
        Extract entities using regex patterns and heuristics.

        Args:
            text: Input text to analyze.

        Returns:
            List of entities extracted via regex.
        """
        entities: list[KnowledgeGraphNode] = []

        # Concrete patterns (EMAIL, URL, PHONE, DATE, MONEY, PERCENT)
        for entity_type, pattern in self.PATTERNS.items():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entity = KnowledgeGraphNode(
                    node_id=str(uuid.uuid4()),
                    label=match.group(0),
                    node_type=entity_type,
                    properties={
                        "start": match.start(),
                        "end": match.end(),
                        "source_text": text[
                            max(0, match.start() - 20) : min(len(text), match.end() + 20)
                        ],
                    },
                )
                entities.append(entity)

        # Heuristic for capitalized phrases (PERSON, ORG, LOCATION, MISC)
        for match in re.finditer(self.CAPITALIZED_PATTERN, text):
            label = match.group(1)
            if label.lower() in {"the", "a", "an", "in", "on", "at", "for", "with", "this", "that"}:
                continue

            entity_type = self._classify_capitalized_phrase(label, text, match.start())
            entity = KnowledgeGraphNode(
                node_id=str(uuid.uuid4()),
                label=label,
                node_type=entity_type,
                properties={
                    "start": match.start(),
                    "end": match.end(),
                    "extraction_method": "regex_heuristic",
                },
            )
            entities.append(entity)

        return entities

    def _classify_capitalized_phrase(
        self, label: str, text: str, start: int
    ) -> str:
        """
        Heuristically classify a capitalized phrase.

        Args:
            label: The matched capitalized phrase.
            text: Full source text.
            start: Start position of the match.

        Returns:
            Estimated entity type (PERSON, ORG, LOCATION, or MISC).
        """
        preceding = text[max(0, start - 30) : start].lower()

        # Person indicators
        if any(indicator in preceding for indicator in [" mr ", " mrs ", " ms ", " dr ", " prof ", " by ", " said ", " according to "]):
            return "PERSON"

        # Organization indicators
        org_suffixes = ["inc", "corp", "ltd", "llc", "company", "university", "institute", "bank", "group", "org", "agency"]
        if any(suffix in label.lower() for suffix in org_suffixes):
            return "ORG"

        # Location indicators
        location_indicators = [" in ", " at ", " from ", " to ", " near ", " city of ", " country of ", " capital of ", " located in "]
        if any(indicator in preceding for indicator in location_indicators):
            return "LOCATION"

        return "MISC"

    async def _extract_with_llm(self, text: str) -> list[KnowledgeGraphNode]:
        """
        Extract entities using the configured LLM service.

        Args:
            text: Input text to analyze.

        Returns:
            List of entities extracted by the LLM.
        """
        prompt = (
            "Extract all named entities from the following text. "
            "For each entity, provide the entity name and type "
            "(PERSON, ORG, LOCATION, DATE, etc.).\n\n"
            f"Text:\n{text}\n\n"
            "Format: ENTITY: <name> | TYPE: <type>"
        )

        response = await self.llm_service.generate(prompt=prompt, temperature=0.3)

        entities: list[KnowledgeGraphNode] = []
        for line in response.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if "ENTITY:" in line and "TYPE:" in line:
                parts = line.split("TYPE:")
                entity_name = parts[0].replace("ENTITY:", "").strip()
                entity_type = parts[1].strip()

                if entity_name and entity_type:
                    entities.append(
                        KnowledgeGraphNode(
                            node_id=str(uuid.uuid4()),
                            label=entity_name,
                            node_type=entity_type,
                            properties={"extracted_by": "llm"},
                        )
                    )

        return entities
