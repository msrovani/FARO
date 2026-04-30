"""
F.A.R.O. OCR Enhancement Service
Enhanced OCR integration with cross-validation and correction suggestions.
"""

import logging
import re
from typing import List, Dict, Optional, Tuple
from difflib import SequenceMatcher
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.db.base import WatchlistEntry, VehicleObservation
from app.services.event_bus import event_bus

logger = logging.getLogger(__name__)


class OcrSource(Enum):
    """OCR source types."""
    MOBILE_AGENT = "mobile_agent"
    STATIC_LPR = "static_lpr"
    MANUAL_INPUT = "manual_input"
    BATCH_PROCESSING = "batch_processing"


@dataclass
class OcrReading:
    """Single OCR reading with metadata."""
    source: OcrSource
    text: str
    confidence: float
    timestamp: str
    location: Optional[Dict[str, float]] = None
    metadata: Optional[Dict] = None


@dataclass
class PlateSuggestion:
    """Plate correction suggestion."""
    original: str
    suggested: str
    confidence: float
    reason: str
    requires_validation: bool


@dataclass
class ValidationResult:
    """Cross-validation result."""
    validated_plate: Optional[str]
    confidence: float
    sources_count: int
    requires_review: bool
    suggestions: List[PlateSuggestion]
    consensus_score: float


class OcrEnhancementService:
    """Enhanced OCR processing with validation and suggestions."""
    
    # Common OCR confusions based on visual similarity
    OCR_CONFUSIONS = {
        '0': 'O', 'O': '0',  # Zero vs Letter O
        '1': 'I', 'I': '1',  # One vs Letter I
        '2': 'Z', 'Z': '2',  # Two vs Letter Z
        '5': 'S', 'S': '5',  # Five vs Letter S
        '8': 'B', 'B': '8',  # Eight vs Letter B
        'G': '6', '6': 'G',  # Six vs Letter G
        'D': '0', '0': 'D',  # Zero vs Letter D
    }
    
    # Brazilian plate format patterns
    PLATE_PATTERNS = [
        r'^[A-Z]{3}\d{4}$',      # ABC1234 (old format)
        r'^[A-Z]{3}\d[A-Z]\d{2}$',  # ABC1D23 (Mercosul format)
        r'^[A-Z]{3}\d{2}[A-Z]$'   # ABC12D (some variations)
    ]
    
    def __init__(self):
        self.cache = {}  # Simple in-memory cache for frequent lookups
        
    async def process_ocr_readings(self, readings: List[OcrReading]) -> ValidationResult:
        """
        Process multiple OCR readings with cross-validation.
        
        Args:
            readings: List of OCR readings from different sources
            
        Returns:
            ValidationResult with consensus and suggestions
        """
        if not readings:
            return ValidationResult(
                validated_plate=None,
                confidence=0.0,
                sources_count=0,
                requires_review=True,
                suggestions=[],
                consensus_score=0.0
            )
        
        # Normalize all readings
        normalized_readings = []
        for reading in readings:
            normalized_text = self.normalize_plate_text(reading.text)
            normalized_readings.append(OcrReading(
                source=reading.source,
                text=normalized_text,
                confidence=reading.confidence,
                timestamp=reading.timestamp,
                location=reading.location,
                metadata=reading.metadata
            ))
        
        # Find consensus plate
        consensus_result = self.find_consensus(normalized_readings)
        
        # Generate suggestions if confidence is low
        suggestions = []
        if consensus_result.confidence < 0.8:
            suggestions = await self.generate_suggestions(normalized_readings)
        
        return ValidationResult(
            validated_plate=consensus_result.plate,
            confidence=consensus_result.confidence,
            sources_count=len(normalized_readings),
            requires_review=consensus_result.confidence < 0.8,
            suggestions=suggestions,
            consensus_score=consensus_result.score
        )
    
    def normalize_plate_text(self, text: str) -> str:
        """
        Normalize plate text for comparison.
        
        Args:
            text: Raw OCR text
            
        Returns:
            Normalized plate text
        """
        # Remove spaces and special characters
        normalized = re.sub(r'[^A-Z0-9]', '', text.upper())
        
        # Basic format validation
        if len(normalized) == 7:
            # Check if it matches old format (ABC1234)
            if re.match(r'^[A-Z]{3}\d{4}$', normalized):
                return normalized
        elif len(normalized) == 8:
            # Check if it matches Mercosul format (ABC1D23)
            if re.match(r'^[A-Z]{3}\d[A-Z]\d{2}$', normalized):
                return normalized
        
        # If no exact match, try to fix common OCR issues
        return self.fix_common_ocr_errors(normalized)
    
    def fix_common_ocr_errors(self, text: str) -> str:
        """
        Fix common OCR errors in plate text.
        
        Args:
            text: Plate text with potential OCR errors
            
        Returns:
            Corrected plate text
        """
        fixed = text
        
        # Apply common confusion fixes
        for wrong, correct in self.OCR_CONFUSIONS.items():
            if wrong in fixed:
                # Check if the correction makes it match a valid pattern
                test_fixed = fixed.replace(wrong, correct)
                if self.is_valid_plate_format(test_fixed):
                    fixed = test_fixed
        
        return fixed
    
    def is_valid_plate_format(self, text: str) -> bool:
        """Check if text matches a valid Brazilian plate format."""
        return any(re.match(pattern, text) for pattern in self.PLATE_PATTERNS)
    
    def find_consensus(self, readings: List[OcrReading]) -> Dict:
        """
        Find consensus plate among multiple readings.
        
        Args:
            readings: List of normalized OCR readings
            
        Returns:
            Dict with plate, confidence, and score
        """
        if not readings:
            return {"plate": None, "confidence": 0.0, "score": 0.0}
        
        # Group readings by text
        text_groups = {}
        for reading in readings:
            if reading.text not in text_groups:
                text_groups[reading.text] = []
            text_groups[reading.text].append(reading)
        
        # Calculate weighted confidence for each group
        best_plate = None
        best_score = 0.0
        best_confidence = 0.0
        
        for text, group in text_groups.items():
            # Weight by confidence and source reliability
            source_weights = {
                OcrSource.MANUAL_INPUT: 1.0,
                OcrSource.STATIC_LPR: 0.9,
                OcrSource.MOBILE_AGENT: 0.8,
                OcrSource.BATCH_PROCESSING: 0.7
            }
            
            weighted_confidence = 0.0
            total_weight = 0.0
            
            for reading in group:
                weight = source_weights.get(reading.source, 0.5)
                weighted_confidence += reading.confidence * weight
                total_weight += weight
            
            avg_confidence = weighted_confidence / total_weight if total_weight > 0 else 0.0
            
            # Calculate consensus score (confidence * frequency)
            frequency_score = len(group) / len(readings)
            consensus_score = avg_confidence * frequency_score
            
            if consensus_score > best_score:
                best_score = consensus_score
                best_plate = text
                best_confidence = avg_confidence
        
        return {
            "plate": best_plate,
            "confidence": best_confidence,
            "score": best_score
        }
    
    async def generate_suggestions(self, readings: List[OcrReading]) -> List[PlateSuggestion]:
        """
        Generate plate correction suggestions.
        
        Args:
            readings: OCR readings with low confidence
            
        Returns:
            List of plate suggestions
        """
        suggestions = []
        
        # Get the most likely reading
        best_reading = max(readings, key=lambda r: r.confidence)
        original_text = best_reading.text
        
        # Generate variations based on common confusions
        variations = self.generate_plate_variations(original_text)
        
        # Check variations against watchlist
        for variation in variations:
            if variation != original_text:
                watchlist_match = await self.check_watchlist_match(variation)
                if watchlist_match:
                    confidence = self.calculate_variation_confidence(
                        original_text, variation, best_reading.confidence
                    )
                    
                    suggestions.append(PlateSuggestion(
                        original=original_text,
                        suggested=variation,
                        confidence=confidence,
                        reason=f"Watchlist match: {watchlist_match['category']}",
                        requires_validation=True
                    ))
        
        # Also suggest based on similar plates in database
        similar_plates = await self.find_similar_plates(original_text)
        for similar_plate, similarity in similar_plates:
            if similarity > 0.7:  # High similarity threshold
                suggestions.append(PlateSuggestion(
                    original=original_text,
                    suggested=similar_plate,
                    confidence=similarity * 0.8,  # Adjust for OCR confidence
                    reason="Similar plate found in database",
                    requires_validation=True
                ))
        
        # Sort by confidence and return top suggestions
        suggestions.sort(key=lambda s: s.confidence, reverse=True)
        return suggestions[:5]  # Return top 5 suggestions
    
    def generate_plate_variations(self, text: str) -> List[str]:
        """
        Generate variations of plate text based on common OCR confusions.
        
        Args:
            text: Original plate text
            
        Returns:
            List of possible variations
        """
        variations = set()
        variations.add(text)
        
        # Generate single-character substitutions
        for i, char in enumerate(text):
            if char in self.OCR_CONFUSIONS:
                replacement = self.OCR_CONFUSIONS[char]
                variation = text[:i] + replacement + text[i+1:]
                if self.is_valid_plate_format(variation):
                    variations.add(variation)
        
        # Generate two-character substitutions for common patterns
        common_pairs = [
            ('0', 'O'), ('1', 'I'), ('2', 'Z'), 
            ('5', 'S'), ('8', 'B'), ('G', '6')
        ]
        
        for wrong, correct in common_pairs:
            if wrong in text:
                # Replace all occurrences
                variation = text.replace(wrong, correct)
                if self.is_valid_plate_format(variation):
                    variations.add(variation)
        
        return list(variations)
    
    async def check_watchlist_match(self, plate: str) -> Optional[Dict]:
        """
        Check if plate matches any watchlist entry.
        
        Args:
            plate: Plate text to check
            
        Returns:
            Watchlist match info or None
        """
        # This would integrate with the existing watchlist system
        # For now, return a placeholder
        cache_key = f"watchlist_{plate}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Placeholder implementation
        # In real implementation, this would query the database
        result = None  # await db.query(WatchlistEntry).filter(...)
        
        self.cache[cache_key] = result
        return result
    
    async def find_similar_plates(self, text: str, threshold: float = 0.7) -> List[Tuple[str, float]]:
        """
        Find similar plates in the database.
        
        Args:
            text: Plate text to compare
            threshold: Similarity threshold
            
        Returns:
            List of (plate, similarity) tuples
        """
        # This would query the database for similar plates
        # For now, return empty list
        return []
    
    def calculate_variation_confidence(self, original: str, variation: str, ocr_confidence: float) -> float:
        """
        Calculate confidence for a plate variation.
        
        Args:
            original: Original OCR text
            variation: Suggested variation
            ocr_confidence: Original OCR confidence
            
        Returns:
            Adjusted confidence score
        """
        # Calculate similarity between original and variation
        similarity = SequenceMatcher(None, original, variation).ratio()
        
        # Adjust confidence based on similarity and OCR confidence
        adjusted_confidence = ocr_confidence * similarity
        
        # Boost confidence if variation matches a valid pattern better
        if self.is_valid_plate_format(variation) and not self.is_valid_plate_format(original):
            adjusted_confidence *= 1.2
        
        return min(adjusted_confidence, 1.0)
    
    async def enhance_watchlist_with_ocr(self, plate_text: str, ocr_confidence: float) -> Optional[Dict]:
        """
        Enhanced watchlist matching with OCR suggestions.
        
        Args:
            plate_text: OCR plate text
            ocr_confidence: OCR confidence score
            
        Returns:
            Enhanced match result or None
        """
        if ocr_confidence >= 0.8:
            # High confidence, proceed with normal watchlist check
            return None
        
        # Low confidence, generate suggestions
        reading = OcrReading(
            source=OcrSource.MOBILE_AGENT,
            text=plate_text,
            confidence=ocr_confidence,
            timestamp="",
            location=None
        )
        
        result = await self.process_ocr_readings([reading])
        
        if result.suggestions:
            best_suggestion = result.suggestions[0]
            return {
                "original": plate_text,
                "suggestion": best_suggestion.suggested,
                "confidence": best_suggestion.confidence,
                "requires_validation": True,
                "reason": best_suggestion.reason
            }
        
        return None


# Global service instance
ocr_enhancement_service = OcrEnhancementService()
