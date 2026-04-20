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


async def evaluate_watchlist(db: AsyncSession, observation: VehicleObservation) -> WatchlistHit | None:
    start_time = time.time()
    plate = observation.plate_number
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
    outcome = AlgorithmOutcome(
        decision=AlgorithmDecision.CRITICAL_MATCH if exact and entry.priority <= 20 else AlgorithmDecision.RELEVANT_MATCH if exact else AlgorithmDecision.WEAK_MATCH,
        confidence=0.95 if exact else 0.62,
        severity="critical" if exact and entry.priority <= 20 else "high" if exact else "moderate",
        explanation=f"Watchlist ativada por correspondencia {'exata' if exact else 'parcial'} com cadastro {entry.category.value}.",
        false_positive_risk="low" if exact else "medium",
        metrics={"watchlist_entry_id": str(entry.id), "priority": entry.priority, "exact_match": exact},
    )
    run = await _register_run(
        db,
        algorithm_type=AlgorithmType.WATCHLIST,
        observation_id=observation.id,
        payload={"plate_number": plate, "payload_version": "v1"},
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

    outcome = AlgorithmOutcome(
        decision=decision,
        confidence=confidence,
        severity=severity,
        explanation=explanation,
        false_positive_risk="medium",
        metrics={
            "distance_km": round(distance_km, 2),
            "travel_time_minutes": round(delta_minutes, 2),
            "plausible_time_minutes": round(plausible_minutes, 2),
            "speed_ratio": round(ratio, 2),
        },
    )
    run = await _register_run(
        db,
        algorithm_type=AlgorithmType.IMPOSSIBLE_TRAVEL,
        observation_id=observation.id,
        payload={"plate_number": observation.plate_number, "payload_version": "v1"},
        outcome=outcome,
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
    outcome = AlgorithmOutcome(
        decision=decision,
        confidence=confidence,
        severity=severity,
        explanation=f"Veiculo observado em regiao de interesse {matched_region.name} com baixa recorrencia historica para a placa.",
        false_positive_risk="medium",
        metrics={"region_id": str(matched_region.id), "recent_count": recent_count},
    )
    run = await _register_run(
        db,
        algorithm_type=AlgorithmType.ROUTE_ANOMALY,
        observation_id=observation.id,
        payload={"plate_number": observation.plate_number, "payload_version": "v1"},
        outcome=outcome,
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
    outcome = AlgorithmOutcome(
        decision=decision,
        confidence=confidence,
        severity=severity,
        explanation=f"Veiculo observado em zona sensivel {matched_zone.name} com {recurrence_count} passagem(ns) nos ultimos 30 dias.",
        false_positive_risk="medium",
        metrics={"zone_id": str(matched_zone.id), "recurrence_count": recurrence_count},
    )
    run = await _register_run(db, algorithm_type=AlgorithmType.SENSITIVE_ZONE_RECURRENCE, observation_id=observation.id, payload={"plate_number": observation.plate_number, "payload_version": "v1"}, outcome=outcome)
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
        outcome = AlgorithmOutcome(
            decision=decision,
            confidence=confidence,
            severity=severity,
            explanation=f"Coocorrencia entre {observation.plate_number} e {neighbor.plate_number} em janela curta com distancia de {distance_km:.2f} km.",
            false_positive_risk="medium",
            metrics={"related_plate": neighbor.plate_number, "cooccurrence_count": historical_count + 1, "distance_km": round(distance_km, 2)},
        )
        run = await _register_run(db, algorithm_type=AlgorithmType.CONVOY, observation_id=observation.id, payload={"plate_number": observation.plate_number, "related_plate": neighbor.plate_number, "payload_version": "v1"}, outcome=outcome)
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
    outcome = AlgorithmOutcome(
        decision=decision,
        confidence=confidence,
        severity=severity,
        explanation=f"Placa reapareceu {recent_count} vez(es) em curto intervalo, indicando comportamento de roaming/loitering.",
        false_positive_risk="medium",
        metrics={"recurrence_count": recent_count, "area_label": area_label},
    )
    run = await _register_run(db, algorithm_type=AlgorithmType.ROAMING, observation_id=observation.id, payload={"plate_number": observation.plate_number, "payload_version": "v1"}, outcome=outcome)
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

