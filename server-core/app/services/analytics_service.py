"""
Heuristic, explainable analytical engine for FARO.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from geoalchemy2.shape import to_shape
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.cache import cached_query
from app.core.observability import record_algorithm_execution, record_suspicion_score_compute

from app.db.base import (
    AlgorithmDecision,
    AlgorithmRun,
    AlgorithmRunStatus,
    AlgorithmType,
    AlgorithmExplanation,
    ConvoyEvent,
    ImpossibleTravelEvent,
    InterceptEvent,
    RoamingEvent,
    RouteAnomalyEvent,
    RouteRegionOfInterest,
    SensitiveAssetRecurrenceEvent,
    SensitiveAssetZone,
    SuspicionScore,
    SuspicionScoreFactor,
    SuspicionReport,
    VehicleObservation,
    WatchlistEntry,
    WatchlistHit,
    WatchlistStatus,
)
from app.services.event_bus import event_bus
from app.services.algorithm_validation_service import algorithm_validation_service


@dataclass
class AlgorithmOutcome:
    decision: AlgorithmDecision
    confidence: float
    severity: str
    explanation: str
    false_positive_risk: str
    metrics: dict[str, Any]


def _distance_km(current: VehicleObservation, previous: VehicleObservation) -> float:
    current_point = to_shape(current.location)
    previous_point = to_shape(previous.location)
    lat_factor = 111.0
    lon_factor = 111.0
    delta_lat = (current_point.y - previous_point.y) * lat_factor
    delta_lon = (current_point.x - previous_point.x) * lon_factor
    return (delta_lat**2 + delta_lon**2) ** 0.5


async def _register_run(
    db: AsyncSession,
    *,
    algorithm_type: AlgorithmType,
    observation_id,
    payload: dict[str, Any],
    outcome: AlgorithmOutcome | None = None,
) -> AlgorithmRun:
    run = AlgorithmRun(
        algorithm_type=algorithm_type,
        observation_id=observation_id,
        run_scope="online",
        status=AlgorithmRunStatus.COMPLETED if outcome else AlgorithmRunStatus.PENDING,
        input_payload=payload,
        output_payload=outcome.metrics if outcome else None,
        executed_at=datetime.utcnow(),
    )
    db.add(run)
    await db.flush()

    if outcome is not None:
        db.add(
            AlgorithmExplanation(
                algorithm_run_id=run.id,
                algorithm_type=algorithm_type,
                decision=outcome.decision,
                confidence=outcome.confidence,
                severity=outcome.severity,
                explanation_text=outcome.explanation,
                false_positive_risk=outcome.false_positive_risk,
            )
        )
    return run


@cached_query(ttl=300)  # 5 minutos
async def get_active_route_regions(db: AsyncSession) -> list[RouteRegionOfInterest]:
    """Get all active route regions of interest (cached)."""
    result = await db.execute(
        select(RouteRegionOfInterest).where(RouteRegionOfInterest.is_active.is_(True))
    )
    return result.scalars().all()


@cached_query(ttl=300)  # 5 minutos
async def get_active_sensitive_zones(db: AsyncSession) -> list[SensitiveAssetZone]:
    """Get all active sensitive zones (cached)."""
    result = await db.execute(
        select(SensitiveAssetZone).where(SensitiveAssetZone.is_active.is_(True))
    )
    return result.scalars().all()


@cached_query(ttl=300)  # 5 minutos
async def get_active_watchlist(db: AsyncSession) -> List[WatchlistEntry]:
    """Get all active watchlist entries (cached)."""
    from app.services.cache_service import cache_service
    
    # Try cache first
    cached_watchlist = await cache_service.get_cached_watchlist()
    if cached_watchlist is not None:
        return cached_watchlist
    
    # Cache miss, query database
    result = await db.execute(
        select(WatchlistEntry).where(WatchlistEntry.status == WatchlistStatus.ACTIVE)
    )
    entries = result.scalars().all()
    
    # Cache the result
    await cache_service.cache_watchlist([{
        "id": str(entry.id),
        "plate_number": entry.plate_number,
        "plate_partial": entry.plate_partial,
        "priority": entry.priority,
        "category": entry.category.value,
        "status": entry.status.value
    } for entry in entries])
    
    return entries


async def evaluate_watchlist(db: AsyncSession, observation: VehicleObservation) -> WatchlistHit | None:
    start_time = time.time()
    plate = observation.plate_number
    
    # Enhanced OCR integration
    ocr_confidence = getattr(observation, 'ocr_confidence', None)
    if ocr_confidence and ocr_confidence < 0.8:
        from app.services.ocr_enhancement_service import ocr_enhancement_service
        ocr_enhancement = await ocr_enhancement_service.enhance_watchlist_with_ocr(plate, ocr_confidence)
        if ocr_enhancement:
            # Use suggested plate for watchlist check
            plate = ocr_enhancement['suggestion']
            logger.info(f"OCR enhancement: {observation.plate_number} → {plate} (confidence: {ocr_enhancement['confidence']:.2f})")
    
    result = await db.execute(
        select(WatchlistEntry)
        .where(WatchlistEntry.status == WatchlistStatus.ACTIVE)
        .where(
            (WatchlistEntry.plate_number == plate)
            | (WatchlistEntry.plate_partial.is_not(None) & WatchlistEntry.plate_partial.ilike(f"%{plate[:4]}%"))
        )
        .order_by(WatchlistEntry.priority.asc())
    )
    entry = result.scalars().first()

    if entry is None:
        await _register_run(
            db,
            algorithm_type=AlgorithmType.WATCHLIST,
            observation_id=observation.id,
            payload={"plate_number": plate, "payload_version": "v1"},
            outcome=AlgorithmOutcome(
                decision=AlgorithmDecision.NO_MATCH,
                confidence=0.0,
                severity="informative",
                explanation="Nenhum cadastro ativo da watchlist correspondeu a placa observada.",
                false_positive_risk="low",
                metrics={},
            ),
        )
        return None

    exact = entry.plate_number == plate if entry.plate_number else False
    
    # Validate with field confirmation history
    validation_result = await algorithm_validation_service.validate_algorithm_result(
        db,
        AlgorithmType.WATCHLIST,
        observation,
        entry,
        original_score=1.0 if exact else 0.62
    )
    
    # Apply validation factor
    validation_factor = validation_result.validation_factor
    
    # Suppress if validation indicates too many false positives
    if validation_result.should_suppress:
        await _register_run(
            db,
            algorithm_type=AlgorithmType.WATCHLIST,
            observation_id=observation.id,
            payload={"plate_number": plate, "payload_version": "v1", "validation_factor": validation_factor},
            outcome=AlgorithmOutcome(
                decision=AlgorithmDecision.NO_MATCH,
                confidence=0.0,
                severity="informative",
                explanation=f"Watchlist match suprimido por validação: {validation_result.reason}",
                false_positive_risk="low",
                metrics={"validation_factor": validation_factor, "suppressed": True},
            ),
        )
        await algorithm_validation_service.record_feedback(
            db, AlgorithmType.WATCHLIST, observation.id, validation_factor, "suppressed"
        )
        return None
    
    # Adjust confidence based on validation
    adjusted_confidence = min(1.0, (0.95 if exact else 0.62) * validation_factor)
    
    outcome = AlgorithmOutcome(
        decision=AlgorithmDecision.CRITICAL_MATCH if exact and entry.priority <= 20 else AlgorithmDecision.RELEVANT_MATCH if exact else AlgorithmDecision.WEAK_MATCH,
        confidence=adjusted_confidence,
        severity="critical" if exact and entry.priority <= 20 else "high" if exact else "moderate",
        explanation=f"Watchlist ativada por correspondencia {'exata' if exact else 'parcial'} com cadastro {entry.category.value}. {validation_result.recommendation}",
        false_positive_risk="low" if exact else "medium",
        metrics={"watchlist_entry_id": str(entry.id), "priority": entry.priority, "exact_match": exact, "validation_factor": validation_factor},
    )
    run = await _register_run(
        db,
        algorithm_type=AlgorithmType.WATCHLIST,
        observation_id=observation.id,
        payload={"plate_number": plate, "payload_version": "v1", "validation_factor": validation_factor},
        outcome=outcome,
    )
    hit = WatchlistHit(
        observation_id=observation.id,
        watchlist_entry_id=entry.id,
        decision=outcome.decision,
        confidence=outcome.confidence,
        severity=outcome.severity,
        explanation=outcome.explanation,
        false_positive_risk=outcome.false_positive_risk,
    )
    db.add(hit)
    
    # Record validation feedback
    decision = "adjusted" if validation_factor != 1.0 else "passed"
    await algorithm_validation_service.record_feedback(
        db, AlgorithmType.WATCHLIST, observation.id, validation_factor, decision
    )
    await event_bus.publish(
        "watchlist_match_evaluated",
        {
            "payload_version": "v1",
            "algorithm_run_id": str(run.id),
            "observation_id": str(observation.id),
            "watchlist_entry_id": str(entry.id),
            "decision": outcome.decision.value,
        },
    )
    
    # Record metrics (Otimização Fase 6)
    duration_seconds = time.time() - start_time
    record_algorithm_execution(
        algorithm_type="watchlist",
        duration_seconds=duration_seconds,
        success=True
    )
    
    return hit


async def evaluate_impossible_travel(db: AsyncSession, observation: VehicleObservation) -> ImpossibleTravelEvent | None:
    start_time = time.time()
    result = await db.execute(
        select(VehicleObservation)
        .where(
            and_(
                VehicleObservation.plate_number == observation.plate_number,
                VehicleObservation.id != observation.id,
                VehicleObservation.observed_at_local >= observation.observed_at_local - timedelta(hours=6),
            )
        )
        .order_by(VehicleObservation.observed_at_local.desc())
        .limit(1)
    )
    previous = result.scalars().first()
    if previous is None:
        return None

    distance_km = _distance_km(observation, previous)
    delta_minutes = max((observation.observed_at_local - previous.observed_at_local).total_seconds() / 60.0, 1.0)
    plausible_minutes = (distance_km / 80.0) * 60.0
    ratio = distance_km / delta_minutes

    if observation.agency_id and previous.agency_id and observation.agency_id != previous.agency_id and delta_minutes < plausible_minutes * 0.8 and distance_km > 50:
        decision = AlgorithmDecision.IMPOSSIBLE
        severity = "critical"
        confidence = 0.95
        explanation = f"ALERTA CLONAGEM MULTI-AGÊNCIA: A placa moveu {distance_km:.1f} km entre jurisdições (agências distintas) em apenas {delta_minutes:.1f} minutos. Impossibilidade física."
    elif delta_minutes < plausible_minutes * 0.5 and distance_km > 120:
        decision = AlgorithmDecision.IMPOSSIBLE
        severity = "critical"
        confidence = 0.87
        explanation = f"A placa apareceu a {distance_km:.1f} km de distancia com intervalo de {delta_minutes:.1f} minutos, abaixo do tempo plausivel de {plausible_minutes:.1f} minutos."
    elif delta_minutes < plausible_minutes * 0.8 and distance_km > 80:
        decision = AlgorithmDecision.HIGHLY_IMPROBABLE
        severity = "high"
        confidence = 0.73
        explanation = f"A placa apareceu a {distance_km:.1f} km de distancia com intervalo de {delta_minutes:.1f} minutos, abaixo do tempo plausivel de {plausible_minutes:.1f} minutos."
    else:
        decision = AlgorithmDecision.ANOMALOUS
        severity = "moderate"
        confidence = 0.51
        explanation = f"A placa apareceu a {distance_km:.1f} km de distancia com intervalo de {delta_minutes:.1f} minutos, abaixo do tempo plausivel de {plausible_minutes:.1f} minutos."

    # Validate with field confirmation history
    validation_result = await algorithm_validation_service.validate_algorithm_result(
        db,
        AlgorithmType.IMPOSSIBLE_TRAVEL,
        observation,
        decision,
        original_score=confidence
    )
    
    # Apply validation factor
    validation_factor = validation_result.validation_factor
    
    # Suppress if validation indicates too many false positives
    if validation_result.should_suppress:
        await _register_run(
            db,
            algorithm_type=AlgorithmType.IMPOSSIBLE_TRAVEL,
            observation_id=observation.id,
            payload={"plate_number": observation.plate_number, "payload_version": "v1", "validation_factor": validation_factor},
            outcome=AlgorithmOutcome(
                decision=AlgorithmDecision.NO_MATCH,
                confidence=0.0,
                severity="informative",
                explanation=f"Impossible travel suprimido por validação: {validation_result.reason}",
                false_positive_risk="low",
                metrics={"validation_factor": validation_factor, "suppressed": True},
            ),
        )
        await algorithm_validation_service.record_feedback(
            db, AlgorithmType.IMPOSSIBLE_TRAVEL, observation.id, validation_factor, "suppressed"
        )
        return None
    
    # Adjust confidence based on validation
    adjusted_confidence = min(1.0, confidence * validation_factor)
    
    outcome = AlgorithmOutcome(
        decision=decision,
        confidence=adjusted_confidence,
        severity=severity,
        explanation=f"{explanation} {validation_result.recommendation}",
        false_positive_risk="medium",
        metrics={
            "distance_km": round(distance_km, 2),
            "travel_time_minutes": round(delta_minutes, 2),
            "plausible_time_minutes": round(plausible_minutes, 2),
            "speed_ratio": round(ratio, 2),
            "validation_factor": validation_factor,
        },
    )
    run = await _register_run(
        db,
        algorithm_type=AlgorithmType.IMPOSSIBLE_TRAVEL,
        observation_id=observation.id,
        payload={"plate_number": observation.plate_number, "payload_version": "v1", "validation_factor": validation_factor},
        outcome=outcome,
    )
    
    # Record validation feedback
    decision_record = "adjusted" if validation_factor != 1.0 else "passed"
    await algorithm_validation_service.record_feedback(
        db, AlgorithmType.IMPOSSIBLE_TRAVEL, observation.id, validation_factor, decision_record
    )
    event = ImpossibleTravelEvent(
        observation_id=observation.id,
        previous_observation_id=previous.id,
        plate_number=observation.plate_number,
        decision=outcome.decision,
        distance_km=outcome.metrics["distance_km"],
        travel_time_minutes=outcome.metrics["travel_time_minutes"],
        plausible_time_minutes=outcome.metrics["plausible_time_minutes"],
        confidence=outcome.confidence,
        severity=outcome.severity,
        explanation=outcome.explanation,
        false_positive_risk=outcome.false_positive_risk,
    )
    db.add(event)
    await event_bus.publish(
        "impossible_travel_evaluated",
        {"payload_version": "v1", "algorithm_run_id": str(run.id), "observation_id": str(observation.id), "decision": outcome.decision.value},
    )
    
    # Record metrics (Otimização Fase 6)
    duration_seconds = time.time() - start_time
    record_algorithm_execution(
        algorithm_type="impossible_travel",
        duration_seconds=duration_seconds,
        success=True
    )
    
    return event


async def evaluate_route_anomaly(db: AsyncSession, observation: VehicleObservation) -> RouteAnomalyEvent | None:
    start_time = time.time()
    regions = await get_active_route_regions(db)
    if not regions:
        return None
    point = to_shape(observation.location)
    matched_region = next((region for region in regions if point.within(to_shape(region.geometry))), None)
    if matched_region is None:
        return None

    recent_count = (
        await db.execute(
            select(func.count(VehicleObservation.id)).where(
                and_(
                    VehicleObservation.plate_number == observation.plate_number,
                    VehicleObservation.observed_at_local >= observation.observed_at_local - timedelta(days=14),
                )
            )
        )
    ).scalar() or 0
    decision = AlgorithmDecision.STRONG_ANOMALY if recent_count <= 1 else AlgorithmDecision.RELEVANT_ANOMALY if recent_count <= 3 else AlgorithmDecision.SLIGHT_DEVIATION
    severity = "high" if decision != AlgorithmDecision.SLIGHT_DEVIATION else "moderate"
    confidence = 0.78 if decision == AlgorithmDecision.STRONG_ANOMALY else 0.61
    
    # Validate with field confirmation history
    validation_result = await algorithm_validation_service.validate_algorithm_result(
        db,
        AlgorithmType.ROUTE_ANOMALY,
        observation,
        decision,
        original_score=confidence
    )
    
    # Apply validation factor
    validation_factor = validation_result.validation_factor
    
    # Suppress if validation indicates too many false positives
    if validation_result.should_suppress:
        await _register_run(
            db,
            algorithm_type=AlgorithmType.ROUTE_ANOMALY,
            observation_id=observation.id,
            payload={"plate_number": observation.plate_number, "payload_version": "v1", "validation_factor": validation_factor},
            outcome=AlgorithmOutcome(
                decision=AlgorithmDecision.NO_MATCH,
                confidence=0.0,
                severity="informative",
                explanation=f"Route anomaly suprimido por validação: {validation_result.reason}",
                false_positive_risk="low",
                metrics={"validation_factor": validation_factor, "suppressed": True},
            ),
        )
        await algorithm_validation_service.record_feedback(
            db, AlgorithmType.ROUTE_ANOMALY, observation.id, validation_factor, "suppressed"
        )
        return None
    
    # Adjust confidence based on validation
    adjusted_confidence = min(1.0, confidence * validation_factor)
    
    outcome = AlgorithmOutcome(
        decision=decision,
        confidence=adjusted_confidence,
        severity=severity,
        explanation=f"Veiculo observado em regiao de interesse {matched_region.name} com baixa recorrencia historica para a placa. {validation_result.recommendation}",
        false_positive_risk="medium",
        metrics={"region_id": str(matched_region.id), "recent_count": recent_count, "validation_factor": validation_factor},
    )
    run = await _register_run(
        db,
        algorithm_type=AlgorithmType.ROUTE_ANOMALY,
        observation_id=observation.id,
        payload={"plate_number": observation.plate_number, "payload_version": "v1", "validation_factor": validation_factor},
        outcome=outcome,
    )
    
    # Record validation feedback
    decision_record = "adjusted" if validation_factor != 1.0 else "passed"
    await algorithm_validation_service.record_feedback(
        db, AlgorithmType.ROUTE_ANOMALY, observation.id, validation_factor, decision_record
    )
    event = RouteAnomalyEvent(
        observation_id=observation.id,
        plate_number=observation.plate_number,
        region_to_id=matched_region.id,
        decision=outcome.decision,
        anomaly_score=1.0 - min(recent_count / 6.0, 1.0),
        confidence=outcome.confidence,
        severity=outcome.severity,
        explanation=outcome.explanation,
        false_positive_risk=outcome.false_positive_risk,
    )
    db.add(event)
    await event_bus.publish(
        "route_anomaly_evaluated",
        {"payload_version": "v1", "algorithm_run_id": str(run.id), "observation_id": str(observation.id), "decision": outcome.decision.value},
    )
    
    # Record metrics (Otimização Fase 6)
    duration_seconds = time.time() - start_time
    record_algorithm_execution(
        algorithm_type="route_anomaly",
        duration_seconds=duration_seconds,
        success=True
    )
    
    return event


async def evaluate_sensitive_zone_recurrence(db: AsyncSession, observation: VehicleObservation) -> SensitiveAssetRecurrenceEvent | None:
    start_time = time.time()
    zones = await get_active_sensitive_zones(db)
    if not zones:
        return None
    point = to_shape(observation.location)
    matched_zone = next((zone for zone in zones if point.within(to_shape(zone.geometry))), None)
    if matched_zone is None:
        return None
    recurrence_count = (
        await db.execute(
            select(func.count(VehicleObservation.id)).where(
                and_(
                    VehicleObservation.plate_number == observation.plate_number,
                    VehicleObservation.observed_at_local >= observation.observed_at_local - timedelta(days=30),
                )
            )
        )
    ).scalar() or 0
    if recurrence_count >= 6:
        decision = AlgorithmDecision.MONITORING_RECOMMENDED
        severity = "high"
        confidence = 0.82
    elif recurrence_count >= 4:
        decision = AlgorithmDecision.RELEVANT_RECURRENCE
        severity = "high"
        confidence = 0.71
    elif recurrence_count >= 2:
        decision = AlgorithmDecision.MEDIUM_RECURRENCE
        severity = "moderate"
        confidence = 0.58
    else:
        decision = AlgorithmDecision.LOW_RECURRENCE
        severity = "informative"
        confidence = 0.42
    
    # Validate with field confirmation history
    validation_result = await algorithm_validation_service.validate_algorithm_result(
        db,
        AlgorithmType.SENSITIVE_ZONE_RECURRENCE,
        observation,
        decision,
        original_score=confidence
    )
    
    # Apply validation factor
    validation_factor = validation_result.validation_factor
    
    # Suppress if validation indicates too many false positives
    if validation_result.should_suppress:
        await _register_run(
            db,
            algorithm_type=AlgorithmType.SENSITIVE_ZONE_RECURRENCE,
            observation_id=observation.id,
            payload={"plate_number": observation.plate_number, "payload_version": "v1", "validation_factor": validation_factor},
            outcome=AlgorithmOutcome(
                decision=AlgorithmDecision.NO_MATCH,
                confidence=0.0,
                severity="informative",
                explanation=f"Sensitive zone recurrence suprimido por validação: {validation_result.reason}",
                false_positive_risk="low",
                metrics={"validation_factor": validation_factor, "suppressed": True},
            ),
        )
        await algorithm_validation_service.record_feedback(
            db, AlgorithmType.SENSITIVE_ZONE_RECURRENCE, observation.id, validation_factor, "suppressed"
        )
        return None
    
    # Adjust confidence based on validation
    adjusted_confidence = min(1.0, confidence * validation_factor)
    
    outcome = AlgorithmOutcome(
        decision=decision,
        confidence=adjusted_confidence,
        severity=severity,
        explanation=f"Veiculo observado em zona sensivel {matched_zone.name} com {recurrence_count} passagem(ns) nos ultimos 30 dias. {validation_result.recommendation}",
        false_positive_risk="medium",
        metrics={"zone_id": str(matched_zone.id), "recurrence_count": recurrence_count, "validation_factor": validation_factor},
    )
    run = await _register_run(db, algorithm_type=AlgorithmType.SENSITIVE_ZONE_RECURRENCE, observation_id=observation.id, payload={"plate_number": observation.plate_number, "payload_version": "v1", "validation_factor": validation_factor}, outcome=outcome)
    
    # Record validation feedback
    decision_record = "adjusted" if validation_factor != 1.0 else "passed"
    await algorithm_validation_service.record_feedback(
        db, AlgorithmType.SENSITIVE_ZONE_RECURRENCE, observation.id, validation_factor, decision_record
    )
    event = SensitiveAssetRecurrenceEvent(
        observation_id=observation.id,
        zone_id=matched_zone.id,
        plate_number=observation.plate_number,
        recurrence_count=recurrence_count,
        decision=outcome.decision,
        confidence=outcome.confidence,
        severity=outcome.severity,
        explanation=outcome.explanation,
        false_positive_risk=outcome.false_positive_risk,
    )
    db.add(event)
    await event_bus.publish("sensitive_zone_recurrence_evaluated", {"payload_version": "v1", "algorithm_run_id": str(run.id), "observation_id": str(observation.id), "decision": outcome.decision.value})
    
    # Record metrics (Otimização Fase 6)
    duration_seconds = time.time() - start_time
    record_algorithm_execution(
        algorithm_type="sensitive_zone_recurrence",
        duration_seconds=duration_seconds,
        success=True
    )
    
    return event


async def evaluate_convoy(db: AsyncSession, observation: VehicleObservation, current_point=None) -> list[ConvoyEvent]:
    start_time = time.time()
    result = await db.execute(
        select(VehicleObservation)
        .where(
            and_(
                VehicleObservation.id != observation.id,
                VehicleObservation.observed_at_local >= observation.observed_at_local - timedelta(minutes=20),
                VehicleObservation.observed_at_local <= observation.observed_at_local + timedelta(minutes=20),
            )
        )
    )
    neighbors = result.scalars().all()
    # Use provided point or convert from location geometry
    if current_point is None:
        current_point = to_shape(observation.location)
    events: list[ConvoyEvent] = []
    
    # Filtrar vizinhos por distância primeiro
    nearby_neighbors = []
    for neighbor in neighbors:
        if neighbor.plate_number == observation.plate_number:
            continue
        # Convert neighbor location geometry to shape to avoid lazy-loading issues
        neighbor_point = to_shape(neighbor.location)
        distance_km = (((current_point.y - neighbor_point.y) * 111.0) ** 2 + ((current_point.x - neighbor_point.x) * 111.0) ** 2) ** 0.5
        if distance_km > 2.0:
            continue
        nearby_neighbors.append((neighbor, distance_km))
    
    if not nearby_neighbors:
        return events
    
    # Single query com GROUP BY para contar histórico de todos os pares
    neighbor_plates = [neighbor.plate_number for neighbor, _ in nearby_neighbors]
    historical_counts_result = await db.execute(
        select(ConvoyEvent.primary_plate, ConvoyEvent.related_plate, func.count(ConvoyEvent.id).label('count'))
        .where(
            and_(
                ConvoyEvent.primary_plate == observation.plate_number,
                ConvoyEvent.related_plate.in_(neighbor_plates)
            )
        )
        .group_by(ConvoyEvent.primary_plate, ConvoyEvent.related_plate)
    )
    
    # Criar mapa de contagens
    count_map = {(row.primary_plate, row.related_plate): row.count for row in historical_counts_result}
    
    # Processar vizinhos sem queries adicionais
    for neighbor, distance_km in nearby_neighbors:
        historical_count = count_map.get((observation.plate_number, neighbor.plate_number), 0)
        decision = AlgorithmDecision.STRONG_CONVOY if historical_count >= 3 else AlgorithmDecision.PROBABLE_CONVOY if historical_count >= 1 else AlgorithmDecision.REPEATED
        severity = "high" if decision != AlgorithmDecision.REPEATED else "moderate"
        confidence = 0.79 if decision == AlgorithmDecision.STRONG_CONVOY else 0.63
        
        # Validate with field confirmation history
        validation_result = await algorithm_validation_service.validate_algorithm_result(
            db,
            AlgorithmType.CONVOY,
            observation,
            decision,
            original_score=confidence
        )
        
        # Apply validation factor
        validation_factor = validation_result.validation_factor
        
        # Suppress if validation indicates too many false positives
        if validation_result.should_suppress:
            await _register_run(
                db,
                algorithm_type=AlgorithmType.CONVOY,
                observation_id=observation.id,
                payload={"plate_number": observation.plate_number, "related_plate": neighbor.plate_number, "payload_version": "v1", "validation_factor": validation_factor},
                outcome=AlgorithmOutcome(
                    decision=AlgorithmDecision.NO_MATCH,
                    confidence=0.0,
                    severity="informative",
                    explanation=f"Convoy suprimido por validação: {validation_result.reason}",
                    false_positive_risk="low",
                    metrics={"validation_factor": validation_factor, "suppressed": True},
                ),
            )
            await algorithm_validation_service.record_feedback(
                db, AlgorithmType.CONVOY, observation.id, validation_factor, "suppressed"
            )
            continue
        
        # Adjust confidence based on validation
        adjusted_confidence = min(1.0, confidence * validation_factor)
        
        outcome = AlgorithmOutcome(
            decision=decision,
            confidence=adjusted_confidence,
            severity=severity,
            explanation=f"Coocorrencia entre {observation.plate_number} e {neighbor.plate_number} em janela curta com distancia de {distance_km:.2f} km. {validation_result.recommendation}",
            false_positive_risk="medium",
            metrics={"related_plate": neighbor.plate_number, "cooccurrence_count": historical_count + 1, "distance_km": round(distance_km, 2), "validation_factor": validation_factor},
        )
        run = await _register_run(db, algorithm_type=AlgorithmType.CONVOY, observation_id=observation.id, payload={"plate_number": observation.plate_number, "related_plate": neighbor.plate_number, "payload_version": "v1", "validation_factor": validation_factor}, outcome=outcome)
        
        # Record validation feedback
        decision_record = "adjusted" if validation_factor != 1.0 else "passed"
        await algorithm_validation_service.record_feedback(
            db, AlgorithmType.CONVOY, observation.id, validation_factor, decision_record
        )
        
        event = ConvoyEvent(
            observation_id=observation.id,
            primary_plate=observation.plate_number,
            related_plate=neighbor.plate_number,
            cooccurrence_count=historical_count + 1,
            decision=outcome.decision,
            confidence=outcome.confidence,
            severity=outcome.severity,
            explanation=outcome.explanation,
            false_positive_risk=outcome.false_positive_risk,
        )
        db.add(event)
        events.append(event)
        await event_bus.publish("convoy_evaluated", {"payload_version": "v1", "algorithm_run_id": str(run.id), "observation_id": str(observation.id), "related_plate": neighbor.plate_number, "decision": outcome.decision.value})
    
    # Record metrics (Otimização Fase 6)
    duration_seconds = time.time() - start_time
    record_algorithm_execution(
        algorithm_type="convoy",
        duration_seconds=duration_seconds,
        success=True
    )
    
    return events


async def evaluate_roaming(db: AsyncSession, observation: VehicleObservation) -> RoamingEvent | None:
    start_time = time.time()
    recent_count = (
        await db.execute(
            select(func.count(VehicleObservation.id)).where(
                and_(
                    VehicleObservation.plate_number == observation.plate_number,
                    VehicleObservation.observed_at_local >= observation.observed_at_local - timedelta(hours=12),
                )
            )
        )
    ).scalar() or 0
    if recent_count < 2:
        return None
    decision = AlgorithmDecision.LIKELY_LOITERING if recent_count >= 6 else AlgorithmDecision.RELEVANT_ROAMING if recent_count >= 4 else AlgorithmDecision.LIGHT_ROAMING
    severity = "high" if decision == AlgorithmDecision.LIKELY_LOITERING else "moderate"
    confidence = 0.77 if decision == AlgorithmDecision.LIKELY_LOITERING else 0.59
    area_label = observation.metadata_snapshot.get("connectivity_type", "area_operacional") if observation.metadata_snapshot else "area_operacional"
    
    # Validate with field confirmation history
    validation_result = await algorithm_validation_service.validate_algorithm_result(
        db,
        AlgorithmType.ROAMING,
        observation,
        decision,
        original_score=confidence
    )
    
    # Apply validation factor
    validation_factor = validation_result.validation_factor
    
    # Suppress if validation indicates too many false positives
    if validation_result.should_suppress:
        await _register_run(
            db,
            algorithm_type=AlgorithmType.ROAMING,
            observation_id=observation.id,
            payload={"plate_number": observation.plate_number, "payload_version": "v1", "validation_factor": validation_factor},
            outcome=AlgorithmOutcome(
                decision=AlgorithmDecision.NO_MATCH,
                confidence=0.0,
                severity="informative",
                explanation=f"Roaming suprimido por validação: {validation_result.reason}",
                false_positive_risk="low",
                metrics={"validation_factor": validation_factor, "suppressed": True},
            ),
        )
        await algorithm_validation_service.record_feedback(
            db, AlgorithmType.ROAMING, observation.id, validation_factor, "suppressed"
        )
        return None
    
    # Adjust confidence based on validation
    adjusted_confidence = min(1.0, confidence * validation_factor)
    
    outcome = AlgorithmOutcome(
        decision=decision,
        confidence=adjusted_confidence,
        severity=severity,
        explanation=f"Placa reapareceu {recent_count} vez(es) em curto intervalo, indicando comportamento de roaming/loitering. {validation_result.recommendation}",
        false_positive_risk="medium",
        metrics={"recurrence_count": recent_count, "area_label": area_label, "validation_factor": validation_factor},
    )
    run = await _register_run(db, algorithm_type=AlgorithmType.ROAMING, observation_id=observation.id, payload={"plate_number": observation.plate_number, "payload_version": "v1", "validation_factor": validation_factor}, outcome=outcome)
    
    # Record validation feedback
    decision_record = "adjusted" if validation_factor != 1.0 else "passed"
    await algorithm_validation_service.record_feedback(
        db, AlgorithmType.ROAMING, observation.id, validation_factor, decision_record
    )
    
    event = RoamingEvent(
        observation_id=observation.id,
        plate_number=observation.plate_number,
        area_label=area_label,
        recurrence_count=recent_count,
        decision=outcome.decision,
        confidence=outcome.confidence,
        severity=outcome.severity,
        explanation=outcome.explanation,
        false_positive_risk=outcome.false_positive_risk,
    )
    db.add(event)
    await event_bus.publish("roaming_evaluated", {"payload_version": "v1", "algorithm_run_id": str(run.id), "observation_id": str(observation.id), "decision": outcome.decision.value})
    
    # Record metrics (Otimização Fase 6)
    duration_seconds = time.time() - start_time
    record_algorithm_execution(
        algorithm_type="roaming",
        duration_seconds=duration_seconds,
        success=True
    )
    
    return event


async def compute_suspicion_score(db: AsyncSession, observation: VehicleObservation) -> SuspicionScore:
    import asyncio
    start_time = time.time()
    
    factors: list[tuple[str, str, float, float, str, str]] = []
    total = 0.0

    # Executar todas as queries em paralelo (são independentes)
    watchlist_result, impossible_result, route_result, sensitive_result, convoy_result, roaming_result, suspicion_result = await asyncio.gather(
        db.execute(select(WatchlistHit).where(WatchlistHit.observation_id == observation.id)),
        db.execute(select(ImpossibleTravelEvent).where(ImpossibleTravelEvent.observation_id == observation.id)),
        db.execute(select(RouteAnomalyEvent).where(RouteAnomalyEvent.observation_id == observation.id)),
        db.execute(select(SensitiveAssetRecurrenceEvent).where(SensitiveAssetRecurrenceEvent.observation_id == observation.id)),
        db.execute(select(func.count(ConvoyEvent.id)).where(ConvoyEvent.observation_id == observation.id)),
        db.execute(select(RoamingEvent).where(RoamingEvent.observation_id == observation.id)),
        db.execute(select(SuspicionReport).where(SuspicionReport.observation_id == observation.id)),
    )
    
    watchlist_hit = watchlist_result.scalars().first()
    if watchlist_hit:
        contribution = 40.0 if watchlist_hit.decision in {AlgorithmDecision.CRITICAL_MATCH, AlgorithmDecision.RELEVANT_MATCH} else 18.0
        total += contribution
        factors.append(("watchlist_match", "watchlist", 1.0, contribution, watchlist_hit.explanation, "positive"))

    impossible_event = impossible_result.scalars().first()
    if impossible_event:
        contribution = 25.0 if impossible_event.decision == AlgorithmDecision.IMPOSSIBLE else 14.0
        total += contribution
        factors.append(("impossible_travel", "impossible_travel", 0.9, contribution, impossible_event.explanation, "positive"))

    route_event = route_result.scalars().first()
    if route_event:
        contribution = 16.0 if route_event.decision in {AlgorithmDecision.STRONG_ANOMALY, AlgorithmDecision.RELEVANT_ANOMALY} else 8.0
        total += contribution
        factors.append(("route_anomaly", "route_anomaly", 0.7, contribution, route_event.explanation, "positive"))

    sensitive_event = sensitive_result.scalars().first()
    if sensitive_event:
        contribution = 18.0 if sensitive_event.recurrence_count >= 4 else 9.0
        total += contribution
        factors.append(("sensitive_zone", "sensitive_zone_recurrence", 0.8, contribution, sensitive_event.explanation, "positive"))

    convoy_count = convoy_result.scalar() or 0
    if convoy_count:
        contribution = min(convoy_count * 6.0, 18.0)
        total += contribution
        factors.append(("convoy", "convoy", 0.7, contribution, f"Coocorrencia detectada com {convoy_count} veiculo(s).", "positive"))

    roaming_event = roaming_result.scalars().first()
    if roaming_event:
        contribution = 12.0 if roaming_event.recurrence_count >= 4 else 6.0
        total += contribution
        factors.append(("roaming", "roaming", 0.6, contribution, roaming_event.explanation, "positive"))

    suspicion_report = suspicion_result.scalars().first()
    if suspicion_report:
        field_contribution = {"low": 4.0, "medium": 8.0, "high": 14.0}[suspicion_report.level.value]
        total += field_contribution
        factors.append(("field_suspicion", "field", 0.5, field_contribution, f"Grau de suspeicao informado pelo campo: {suspicion_report.level.value}.", "positive"))

    score = min(total, 100.0)
    if score >= 80:
        label = AlgorithmDecision.CRITICAL
        severity = "critical"
    elif score >= 60:
        label = AlgorithmDecision.HIGH_RISK
        severity = "high"
    elif score >= 40:
        label = AlgorithmDecision.RELEVANT
        severity = "high"
    elif score >= 20:
        label = AlgorithmDecision.MONITOR
        severity = "moderate"
    else:
        label = AlgorithmDecision.INFORMATIVE
        severity = "informative"

    explanation = "Score composto calculado a partir de fatores heuristicos explicaveis."
    score_row = (
        await db.execute(select(SuspicionScore).where(SuspicionScore.observation_id == observation.id))
    ).scalars().first()
    if score_row is None:
        score_row = SuspicionScore(
            observation_id=observation.id,
            plate_number=observation.plate_number,
            final_score=score,
            final_label=label,
            confidence=0.78 if factors else 0.3,
            severity=severity,
            explanation=explanation,
            false_positive_risk="medium" if factors else "high",
        )
        db.add(score_row)
        await db.flush()
    else:
        score_row.plate_number = observation.plate_number
        score_row.final_score = score
        score_row.final_label = label
        score_row.confidence = 0.78 if factors else 0.3
        score_row.severity = severity
        score_row.explanation = explanation
        score_row.false_positive_risk = "medium" if factors else "high"
        previous_factors = (
            await db.execute(
                select(SuspicionScoreFactor).where(
                    SuspicionScoreFactor.suspicion_score_id == score_row.id
                )
            )
        ).scalars().all()
        for factor in previous_factors:
            await db.delete(factor)
        await db.flush()

    for name, source, weight, contribution, factor_explanation, direction in factors:
        db.add(
            SuspicionScoreFactor(
                suspicion_score_id=score_row.id,
                factor_name=name,
                factor_source=source,
                weight=weight,
                contribution=contribution,
                explanation=factor_explanation,
                direction=direction,
            )
        )

    run = await _register_run(
        db,
        algorithm_type=AlgorithmType.COMPOSITE_SCORE,
        observation_id=observation.id,
        payload={"plate_number": observation.plate_number, "payload_version": "v1"},
        outcome=AlgorithmOutcome(
            decision=label,
            confidence=score_row.confidence,
            severity=severity,
            explanation=explanation,
            false_positive_risk=score_row.false_positive_risk,
            metrics={"final_score": score, "factors": len(factors)},
        ),
    )
    await event_bus.publish("suspicion_score_computed", {"payload_version": "v1", "algorithm_run_id": str(run.id), "observation_id": str(observation.id), "decision": label.value, "score": score})
    
    # Record metrics (Otimização Fase 6)
    duration_seconds = time.time() - start_time
    record_suspicion_score_compute(duration_seconds=duration_seconds)
    
    return score_row


async def evaluate_intercept_algorithm(db: AsyncSession, observation: VehicleObservation) -> InterceptEvent | None:
    """
    INTERCEPT algorithm - Combined analysis for approach recommendations.
    
    Combines multiple algorithm signals to determine if a vehicle should be approached.
    """
    start_time = time.time()
    
    # Get individual algorithm results
    watchlist_result = await evaluate_watchlist(db, observation)
    impossible_travel_result = await evaluate_impossible_travel(db, observation)
    route_anomaly_result = await evaluate_route_anomaly(db, observation)
    sensitive_zone_result = await evaluate_sensitive_zone_recurrence(db, observation)
    roaming_result = await evaluate_roaming(db, observation)
    
    # Convert location geometry to shape for convoy evaluation
    from geoalchemy2.shape import to_shape
    current_point = to_shape(observation.location)
    convoy_result = await evaluate_convoy(db, observation, current_point)
    
    # Get adaptive weights based on context and performance
    from app.services.intercept_adaptive_service import intercept_adaptive_service
    
    context = {
        "hour": observation.observed_at_local.hour,
        "location_type": await determine_location_type(db, observation.location),
        "vehicle_type": getattr(observation, 'vehicle_type', 'unknown')
    }
    
    adaptive_weights = await intercept_adaptive_service.get_adaptive_weights(db, context)
    
    # Calculate individual scores (0.0 to 1.0)
    watchlist_score = 0.8 if watchlist_result else 0.0
    impossible_travel_score = 0.9 if impossible_travel_result and impossible_travel_result.decision in [AlgorithmDecision.IMPOSSIBLE, AlgorithmDecision.HIGHLY_IMPROBABLE] else 0.0
    route_anomaly_score = 0.7 if route_anomaly_result else 0.0
    sensitive_zone_score = 0.8 if sensitive_zone_result else 0.0
    convoy_score = 0.6 if convoy_result else 0.0
    roaming_score = 0.5 if roaming_result else 0.0
    
    # Validate INTERCEPT with field confirmation history
    validation_result = await algorithm_validation_service.validate_algorithm_result(
        db,
        AlgorithmType.INTERCEPT,
        observation,
        {"watchlist": watchlist_score, "impossible_travel": impossible_travel_score},
        original_score=None  # Score calculado depois
    )
    
    # Apply validation factor to individual scores
    validation_factor = validation_result.validation_factor
    
    # Suppress if validation indicates too many false positives
    if validation_result.should_suppress:
        logger.info(f"INTERCEPT suprimido por validação para placa {observation.plate_number}: {validation_result.reason}")
        # Create suppressed intercept event
        intercept_event = InterceptEvent(
            observation_id=observation.id,
            intercept_score=0.0,
            watchlist_trigger=watchlist_result is not None,
            route_anomaly_trigger=route_anomaly_result is not None,
            impossible_travel_trigger=impossible_travel_result is not None and impossible_travel_result.decision in [AlgorithmDecision.IMPOSSIBLE, AlgorithmDecision.HIGHLY_IMPROBABLE],
            sensitive_zone_trigger=sensitive_zone_result is not None,
            convoy_trigger=convoy_result is not None,
            roaming_trigger=roaming_result is not None,
            watchlist_score=watchlist_score if watchlist_score > 0 else None,
            route_anomaly_score=route_anomaly_score if route_anomaly_score > 0 else None,
            impossible_travel_score=impossible_travel_score if impossible_travel_score > 0 else None,
            sensitive_zone_score=sensitive_zone_score if sensitive_zone_score > 0 else None,
            convoy_score=convoy_score if convoy_score > 0 else None,
            roaming_score=roaming_score if roaming_score > 0 else None,
            decision=AlgorithmDecision.IGNORE_RECOMMENDED,
            confidence=0.0,
            severity="informative",
            explanation=f"INTERCEPT suprimido por validação: {validation_result.reason}",
            false_positive_risk="low",
            recommendation="IGNORE",
            priority_level="low",
            time_of_day_risk=time_of_day_risk,
            day_of_week_risk=day_of_week_risk,
            nearby_critical_assets=None,
            proximity_sensitive_zone=sensitive_zone_result is not None,
        )
        
        db.add(intercept_event)
        await db.flush()
        
        await algorithm_validation_service.record_feedback(
            db, AlgorithmType.INTERCEPT, observation.id, validation_factor, "suppressed"
        )
        
        return intercept_event
    
    # Apply validation factor to scores
    watchlist_score *= validation_factor
    impossible_travel_score *= validation_factor
    route_anomaly_score *= validation_factor
    sensitive_zone_score *= validation_factor
    convoy_score *= validation_factor
    roaming_score *= validation_factor
    
    # Time-based risk factors
    current_hour = observation.observed_at_local.hour
    time_of_day_risk = 1.0 if 22 <= current_hour or current_hour <= 5 else 0.5  # Higher risk at night
    
    current_day = observation.observed_at_local.weekday()
    day_of_week_risk = 0.8 if current_day >= 5 else 0.5  # Higher risk on weekends
    
    # Calculate combined intercept score with adaptive weights
    intercept_score = (
        watchlist_score * adaptive_weights.watchlist +
        impossible_travel_score * adaptive_weights.impossible_travel +
        route_anomaly_score * adaptive_weights.route_anomaly +
        sensitive_zone_score * adaptive_weights.sensitive_zone +
        convoy_score * adaptive_weights.convoy +
        roaming_score * adaptive_weights.roaming
    ) * max(time_of_day_risk, day_of_week_risk)
    
    # Determine recommendation based on score
    if intercept_score >= 0.8:
        decision = AlgorithmDecision.APPROACH_RECOMMENDED
        recommendation = "APPROACH"
        priority_level = "high"
        severity = "critical"
        confidence = min(intercept_score + 0.1, 1.0)
        explanation = f"ALTO RISCO DE ABORDAGEM: Múltiplos indicadores de atividade suspeita combinados com fatores de risco temporal. Pesos adaptativos: {adaptive_weights.__dict__}. {validation_result.recommendation}"
    elif intercept_score >= 0.6:
        decision = AlgorithmDecision.MONITOR_RECOMMENDED
        recommendation = "MONITOR"
        priority_level = "medium"
        severity = "high"
        confidence = intercept_score
        explanation = f"MONITORAMENTO RECOMENDADO: Indicadores moderados de suspeita justificam acompanhamento. {validation_result.recommendation}"
    else:
        decision = AlgorithmDecision.IGNORE_RECOMMENDED
        recommendation = "IGNORE"
        priority_level = "low"
        severity = "moderate"
        confidence = 1.0 - intercept_score
        explanation = f"BAIXO RISCO: Sem indicadores suficientes para ação imediata. {validation_result.recommendation}"
    
    # Create intercept event
    intercept_event = InterceptEvent(
        observation_id=observation.id,
        intercept_score=intercept_score,
        watchlist_trigger=watchlist_result is not None,
        route_anomaly_trigger=route_anomaly_result is not None,
        impossible_travel_trigger=impossible_travel_result is not None and impossible_travel_result.decision in [AlgorithmDecision.IMPOSSIBLE, AlgorithmDecision.HIGHLY_IMPROBABLE],
        sensitive_zone_trigger=sensitive_zone_result is not None,
        convoy_trigger=convoy_result is not None,
        roaming_trigger=roaming_result is not None,
        watchlist_score=watchlist_score if watchlist_score > 0 else None,
        route_anomaly_score=route_anomaly_score if route_anomaly_score > 0 else None,
        impossible_travel_score=impossible_travel_score if impossible_travel_score > 0 else None,
        sensitive_zone_score=sensitive_zone_score if sensitive_zone_score > 0 else None,
        convoy_score=convoy_score if convoy_score > 0 else None,
        roaming_score=roaming_score if roaming_score > 0 else None,
        decision=decision,
        confidence=confidence,
        severity=severity,
        explanation=explanation,
        false_positive_risk="low" if intercept_score >= 0.8 else "medium" if intercept_score >= 0.6 else "high",
        recommendation=recommendation,
        priority_level=priority_level,
        time_of_day_risk=time_of_day_risk,
        day_of_week_risk=day_of_week_risk,
        nearby_critical_assets=None,  # TODO: Implement nearby assets check
        proximity_sensitive_zone=sensitive_zone_result is not None,
    )
    
    db.add(intercept_event)
    await db.flush()
    
    # Register validation feedback for INTERCEPT
    decision_record = "adjusted" if validation_factor != 1.0 else "passed"
    await algorithm_validation_service.record_feedback(
        db, AlgorithmType.INTERCEPT, observation.id, validation_factor, decision_record
    )
    
    # Register algorithm run
    run = await _register_run(
        db,
        algorithm_type=AlgorithmType.INTERCEPT,
        observation_id=observation.id,
        payload={
            "plate_number": observation.plate_number,
            "individual_scores": {
                "watchlist": watchlist_score,
                "impossible_travel": impossible_travel_score,
                "route_anomaly": route_anomaly_score,
                "sensitive_zone": sensitive_zone_score,
                "convoy": convoy_score,
                "roaming": roaming_score,
            },
            "time_factors": {
                "time_of_day_risk": time_of_day_risk,
                "day_of_week_risk": day_of_week_risk,
            }
        },
        outcome=AlgorithmOutcome(
            decision=decision,
            confidence=confidence,
            severity=severity,
            explanation=explanation,
            false_positive_risk="low" if intercept_score >= 0.8 else "medium" if intercept_score >= 0.6 else "high",
            metrics={
                "intercept_score": intercept_score,
                "recommendation": recommendation,
                "triggers_count": sum([
                    watchlist_result is not None,
                    route_anomaly_result is not None,
                    impossible_travel_result is not None and impossible_travel_result.decision in [AlgorithmDecision.IMPOSSIBLE, AlgorithmDecision.HIGHLY_IMPROBABLE],
                    sensitive_zone_result is not None,
                    convoy_result is not None,
                    roaming_result is not None,
                ])
            }
        )
    )
    
    # Record metrics
    duration_seconds = time.time() - start_time
    record_algorithm_execution(
        algorithm_type="intercept",
        duration_seconds=duration_seconds,
        success=True
    )
    
    # Create location-based alerts if high priority
    if intercept_event.recommendation in ["APPROACH", "MONITOR"]:
        from app.services.location_interception_service import create_location_based_alerts
        await create_location_based_alerts(db, intercept_event, observation)
    
    return intercept_event


async def determine_location_type(db: AsyncSession, location) -> str:
    """Determine if location is urban or highway based on context."""
    from geoalchemy2.shape import to_shape
    
    point = to_shape(location)
    
    # Check if near major highways (simplified logic)
    # In real implementation would use GIS data for road networks
    highway_keywords = ["rodovia", "highway", "br-", "sp-", "rj-"]
    
    # For now, use a simple heuristic based on location density
    # Check if there are many recent observations nearby (urban indicator)
    recent_observations = await db.execute(
        select(func.count(VehicleObservation.id))
        .where(
            and_(
                VehicleObservation.location == location,
                VehicleObservation.observed_at_local >= datetime.utcnow() - timedelta(hours=1)
            )
        )
    ).scalar() or 0
    
    if recent_observations > 10:
        return "urban"
    else:
        return "highway"


async def evaluate_observation_algorithms(db: AsyncSession, observation: VehicleObservation) -> None:
    # Run algorithms sequentially to avoid concurrent flush issues
    await evaluate_watchlist(db, observation)
    await evaluate_impossible_travel(db, observation)
    await evaluate_route_anomaly(db, observation)
    await evaluate_sensitive_zone_recurrence(db, observation)
    await evaluate_roaming(db, observation)

    # Convert location geometry to shape before passing to avoid lazy-loading issues
    from geoalchemy2.shape import to_shape
    current_point = to_shape(observation.location)
    await evaluate_convoy(db, observation, current_point)

    # Score composto (depende de todos os eventos)
    await compute_suspicion_score(db, observation)
    
    # Run INTERCEPT algorithm after all individual algorithms
    await evaluate_intercept_algorithm(db, observation)

