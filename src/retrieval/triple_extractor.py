"""
Triple extraction module for Subject-Predicate-Object extraction.

Provides simple sentence-parsing based triple extraction with optional
LLM enhancement to build structured knowledge graph relationships from text.
"""

import re
import uuid
from typing import Optional

from src.core.types import KnowledgeGraphNode, KnowledgeGraphEdge
from src.core.logger import get_logger
from src.services.llm_service import LLMService

logger = get_logger(__name__)


class TripleExtractor:
    """
    Extract (subject, predicate, object) triples from text.

    Uses simple sentence-level SVO heuristics as a baseline and optionally
    leverages an LLM for higher-quality triple extraction.
    """

    # Simple SVO patterns for English sentences
    SVO_PATTERNS = [
        (
            r"([A-Z][a-zA-Z\s]+?)\s+"
            r"(is|are|was|were|has|have|had|does|do|did|can|could|will|would|"
            r"shall|should|may|might|must)\s+"
            r"([a-zA-Z\s]+)"
        ),
        (
            r"([A-Z][a-zA-Z\s]+?)\s+"
            r"(acquired|bought|sold|founded|established|developed|created|built|"
            r"designed|managed|led|owns|operates|partners with|collaborates with)\s+"
            r"([a-zA-Z\s]+)"
        ),
    ]

    def __init__(self, llm_service: Optional[LLMService] = None):
        """
        Initialize the triple extractor.

        Args:
            llm_service: Optional LLM service for advanced triple extraction.
        """
        self.llm_service = llm_service
        self.logger = get_logger(self.__class__.__name__)

    async def extract_triples(
        self, text: str
    ) -> list[tuple[KnowledgeGraphNode, KnowledgeGraphEdge, KnowledgeGraphNode]]:
        """
        Extract subject-predicate-object triples from the given text.

        Regex-based extraction is performed first. If an LLM service is
        configured, its output is merged into the result set. Duplicates
        are removed based on a lower-cased (subject, predicate, object) key.

        Args:
            text: Input text to analyze.

        Returns:
            A list of ``(subject_node, edge, object_node)`` tuples.
        """
        try:
            triples: list[tuple[KnowledgeGraphNode, KnowledgeGraphEdge, KnowledgeGraphNode]] = []

            # Simple sentence / regex extraction
            regex_triples = self._extract_with_regex(text)
            triples.extend(regex_triples)

            # LLM augmentation / fallback
            if self.llm_service is not None:
                try:
                    llm_triples = await self._extract_with_llm(text)
                    if llm_triples:
                        triples.extend(llm_triples)
                except Exception as exc:
                    self.logger.warning(f"LLM triple extraction failed: {exc}")

            # Deduplicate by (subject_lower, predicate_lower, object_lower)
            seen: set[tuple[str, str, str]] = set()
            unique_triples: list[
                tuple[KnowledgeGraphNode, KnowledgeGraphEdge, KnowledgeGraphNode]
            ] = []
            for subj, edge, obj in triples:
                key = (
                    subj.label.lower(),
                    edge.relationship_type.lower(),
                    obj.label.lower(),
                )
                if key not in seen:
                    seen.add(key)
                    unique_triples.append((subj, edge, obj))

            self.logger.info(f"Extracted {len(unique_triples)} unique triples")
            return unique_triples

        except Exception as exc:
            self.logger.error(f"Triple extraction failed: {exc}")
            return []

    def _extract_with_regex(
        self, text: str
    ) -> list[tuple[KnowledgeGraphNode, KnowledgeGraphEdge, KnowledgeGraphNode]]:
        """
        Extract triples using simple sentence parsing and regex patterns.

        Args:
            text: Input text to analyze.

        Returns:
            List of triples extracted via regex heuristics.
        """
        triples: list[tuple[KnowledgeGraphNode, KnowledgeGraphEdge, KnowledgeGraphNode]] = []
        sentences = re.split(r"(?<=[.!?])\s+", text)

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            for pattern in self.SVO_PATTERNS:
                for match in re.finditer(pattern, sentence):
                    subj_text = match.group(1).strip()
                    pred_text = match.group(2).strip()
                    obj_text = match.group(3).strip()

                    # Strip trailing punctuation from the object
                    obj_text = re.sub(r"[.!?;,]$", "", obj_text).strip()

                    if len(subj_text) < 2 or len(obj_text) < 2:
                        continue

                    subj = KnowledgeGraphNode(
                        node_id=str(uuid.uuid4()),
                        label=subj_text,
                        node_type="ENTITY",
                        properties={"source_sentence": sentence},
                    )
                    obj = KnowledgeGraphNode(
                        node_id=str(uuid.uuid4()),
                        label=obj_text,
                        node_type="ENTITY",
                        properties={"source_sentence": sentence},
                    )
                    edge = KnowledgeGraphEdge(
                        edge_id=str(uuid.uuid4()),
                        source_node_id=subj.node_id,
                        target_node_id=obj.node_id,
                        relationship_type=pred_text.upper(),
                        properties={"source_sentence": sentence},
                    )
                    triples.append((subj, edge, obj))

        return triples

    async def _extract_with_llm(
        self, text: str
    ) -> list[tuple[KnowledgeGraphNode, KnowledgeGraphEdge, KnowledgeGraphNode]]:
        """
        Extract triples using the configured LLM service.

        Args:
            text: Input text to analyze.

        Returns:
            List of triples extracted by the LLM.
        """
        prompt = (
            "Extract subject-predicate-object triples from the following text. "
            "For each triple, provide:\n"
            "SUBJECT | PREDICATE | OBJECT\n\n"
            f"Text:\n{text}\n\n"
            "Triples:"
        )

        response = await self.llm_service.generate(prompt=prompt, temperature=0.3)
        triples: list[tuple[KnowledgeGraphNode, KnowledgeGraphEdge, KnowledgeGraphNode]] = []

        for line in response.split("\n"):
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue

            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 3:
                subj_text, pred_text, obj_text = parts[0], parts[1], parts[2]

                if not subj_text or not pred_text or not obj_text:
                    continue

                subj = KnowledgeGraphNode(
                    node_id=str(uuid.uuid4()),
                    label=subj_text,
                    node_type="ENTITY",
                    properties={"extracted_by": "llm"},
                )
                obj = KnowledgeGraphNode(
                    node_id=str(uuid.uuid4()),
                    label=obj_text,
                    node_type="ENTITY",
                    properties={"extracted_by": "llm"},
                )
                edge = KnowledgeGraphEdge(
                    edge_id=str(uuid.uuid4()),
                    source_node_id=subj.node_id,
                    target_node_id=obj.node_id,
                    relationship_type=pred_text.upper(),
                    properties={"extracted_by": "llm"},
                )
                triples.append((subj, edge, obj))

        return triples
