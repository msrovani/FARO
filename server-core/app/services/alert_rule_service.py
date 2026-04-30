"""
Alert Rule Service - Business logic for alert rule management.
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from app.db.base import AlertRule, AlertRuleTypeEnum, AlertRuleSeverityEnum, User
from app.schemas.alert_rules import (
    AlertRuleCreate,
    AlertRuleUpdate,
    AlertRuleResponse,
    AlertRuleStatsResponse,
)


async def create_alert_rule(
    db: AsyncSession,
    rule_data: AlertRuleCreate,
    created_by: UUID,
    agency_id: Optional[UUID] = None,
) -> AlertRuleResponse:
    """
    Create a new alert rule.
    
    Args:
        db: Database session
        rule_data: Alert rule data
        created_by: User ID who created the rule
        agency_id: Agency ID (null for global rules)
    
    Returns:
        Created alert rule
    """
    rule = AlertRule(
        name=rule_data.name,
        description=rule_data.description,
        rule_type=rule_data.rule_type,
        conditions=rule_data.conditions,
        severity=rule_data.severity,
        is_active=rule_data.is_active,
        priority=rule_data.priority,
        agency_id=agency_id,
        created_by=created_by,
    )
    
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    
    return AlertRuleResponse.model_validate(rule)


async def get_alert_rule(
    db: AsyncSession,
    rule_id: UUID,
) -> Optional[AlertRuleResponse]:
    """
    Get a specific alert rule by ID.
    
    Args:
        db: Database session
        rule_id: Alert rule ID
    
    Returns:
        Alert rule or None if not found
    """
    result = await db.execute(
        select(AlertRule).where(AlertRule.id == rule_id)
    )
    rule = result.scalar_one_or_none()
    
    if not rule:
        return None
    
    return AlertRuleResponse.model_validate(rule)


async def list_alert_rules(
    db: AsyncSession,
    agency_id: Optional[UUID] = None,
    rule_type: Optional[AlertRuleTypeEnum] = None,
    is_active: Optional[bool] = None,
    severity: Optional[AlertRuleSeverityEnum] = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[List[AlertRuleResponse], int]:
    """
    List alert rules with filters.
    
    Args:
        db: Database session
        agency_id: Filter by agency (null = global rules only)
        rule_type: Filter by rule type
        is_active: Filter by active status
        severity: Filter by severity
        limit: Maximum number of results
        offset: Offset for pagination
    
    Returns:
        Tuple of (list of rules, total count)
    """
    # Build query
    query = select(AlertRule)
    
    # Apply filters
    conditions = []
    
    if agency_id is not None:
        # Rules for specific agency OR global rules
        conditions.append(
            or_(
                AlertRule.agency_id == agency_id,
                AlertRule.agency_id.is_(None)
            )
        )
    else:
        # Only global rules
        conditions.append(AlertRule.agency_id.is_(None))
    
    if rule_type is not None:
        conditions.append(AlertRule.rule_type == rule_type)
    
    if is_active is not None:
        conditions.append(AlertRule.is_active == is_active)
    
    if severity is not None:
        conditions.append(AlertRule.severity == severity)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    # Order by priority (descending) and created_at (descending)
    query = query.order_by(AlertRule.priority.desc(), AlertRule.created_at.desc())
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    query = query.limit(limit).offset(offset)
    
    result = await db.execute(query)
    rules = result.scalars().all()
    
    return [AlertRuleResponse.model_validate(rule) for rule in rules], total


async def update_alert_rule(
    db: AsyncSession,
    rule_id: UUID,
    rule_data: AlertRuleUpdate,
) -> Optional[AlertRuleResponse]:
    """
    Update an existing alert rule.
    
    Args:
        db: Database session
        rule_id: Alert rule ID
        rule_data: Updated rule data
    
    Returns:
        Updated alert rule or None if not found
    """
    result = await db.execute(
        select(AlertRule).where(AlertRule.id == rule_id)
    )
    rule = result.scalar_one_or_none()
    
    if not rule:
        return None
    
    # Update fields
    if rule_data.name is not None:
        rule.name = rule_data.name
    if rule_data.description is not None:
        rule.description = rule_data.description
    if rule_data.conditions is not None:
        rule.conditions = rule_data.conditions
    if rule_data.severity is not None:
        rule.severity = rule_data.severity
    if rule_data.is_active is not None:
        rule.is_active = rule_data.is_active
    if rule_data.priority is not None:
        rule.priority = rule_data.priority
    
    rule.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(rule)
    
    return AlertRuleResponse.model_validate(rule)


async def delete_alert_rule(
    db: AsyncSession,
    rule_id: UUID,
) -> bool:
    """
    Delete an alert rule.
    
    Args:
        db: Database session
        rule_id: Alert rule ID
    
    Returns:
        True if deleted, False if not found
    """
    result = await db.execute(
        select(AlertRule).where(AlertRule.id == rule_id)
    )
    rule = result.scalar_one_or_none()
    
    if not rule:
        return False
    
    await db.delete(rule)
    await db.commit()
    
    return True


async def increment_rule_trigger_count(
    db: AsyncSession,
    rule_id: UUID,
) -> bool:
    """
    Increment the trigger count for a rule and update last_triggered_at.
    
    Args:
        db: Database session
        rule_id: Alert rule ID
    
    Returns:
        True if updated, False if not found
    """
    result = await db.execute(
        select(AlertRule).where(AlertRule.id == rule_id)
    )
    rule = result.scalar_one_or_none()
    
    if not rule:
        return False
    
    rule.times_triggered += 1
    rule.last_triggered_at = datetime.utcnow()
    
    await db.commit()
    
    return True


async def get_alert_rule_stats(
    db: AsyncSession,
    agency_id: Optional[UUID] = None,
) -> AlertRuleStatsResponse:
    """
    Get statistics about alert rules.
    
    Args:
        db: Database session
        agency_id: Agency ID (null = global stats)
    
    Returns:
        Alert rule statistics
    """
    # Build base query
    query = select(AlertRule)
    
    if agency_id is not None:
        query = query.where(
            or_(
                AlertRule.agency_id == agency_id,
                AlertRule.agency_id.is_(None)
            )
        )
    else:
        query = query.where(AlertRule.agency_id.is_(None))
    
    # Total rules
    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar()
    
    # Active rules
    active_query = query.where(AlertRule.is_active == True)
    active_result = await db.execute(select(func.count()).select_from(active_query.subquery()))
    active = active_result.scalar()
    
    # Inactive rules
    inactive = total - active
    
    # Rules by type
    type_query = select(
        AlertRule.rule_type,
        func.count(AlertRule.id)
    ).select_from(query.subquery()).group_by(AlertRule.rule_type)
    type_result = await db.execute(type_query)
    rules_by_type = {row[0].value: row[1] for row in type_result.all()}
    
    # Rules by severity
    severity_query = select(
        AlertRule.severity,
        func.count(AlertRule.id)
    ).select_from(query.subquery()).group_by(AlertRule.severity)
    severity_result = await db.execute(severity_query)
    rules_by_severity = {row[0].value: row[1] for row in severity_result.all()}
    
    # Most triggered rules
    most_triggered_query = query.order_by(
        AlertRule.times_triggered.desc()
    ).limit(10)
    most_triggered_result = await db.execute(most_triggered_query)
    most_triggered = [
        {
            "id": str(rule.id),
            "name": rule.name,
            "times_triggered": rule.times_triggered,
            "last_triggered_at": rule.last_triggered_at.isoformat() if rule.last_triggered_at else None,
        }
        for rule in most_triggered_result.scalars().all()
    ]
    
    return AlertRuleStatsResponse(
        total_rules=total,
        active_rules=active,
        inactive_rules=inactive,
        rules_by_type=rules_by_type,
        rules_by_severity=rules_by_severity,
        most_triggered=most_triggered,
    )


async def get_active_rules_for_observation(
    db: AsyncSession,
    agency_id: UUID,
) -> List[AlertRule]:
    """
    Get all active rules for a specific agency (including global rules).
    
    Args:
        db: Database session
        agency_id: Agency ID
    
    Returns:
        List of active alert rules ordered by priority
    """
    query = select(AlertRule).where(
        and_(
            AlertRule.is_active == True,
            or_(
                AlertRule.agency_id == agency_id,
                AlertRule.agency_id.is_(None)
            )
        )
    ).order_by(AlertRule.priority.desc())
    
    result = await db.execute(query)
    return result.scalars().all()
