"""
Agency Hierarchy Service - Business logic for agency hierarchy filtering.
"""
from typing import List, Optional, Set
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.db.base import Agency, AgencyType


async def get_agency_with_hierarchy(
    db: AsyncSession,
    agency_id: UUID,
) -> Optional[Agency]:
    """
    Load agency with hierarchy information.
    
    Args:
        db: Database session
        agency_id: Agency ID
    
    Returns:
        Agency object or None if not found
    """
    result = await db.execute(
        select(Agency).where(Agency.id == agency_id)
    )
    return result.scalar_one_or_none()


async def get_child_agency_ids(
    db: AsyncSession,
    parent_agency_id: UUID,
    recursive: bool = True,
) -> List[UUID]:
    """
    Get all child agency IDs for a parent agency.
    
    Args:
        db: Database session
        parent_agency_id: Parent agency ID
        recursive: If True, include all descendants (not just direct children)
    
    Returns:
        List of child agency IDs
    """
    if recursive:
        # Get all descendants recursively
        child_ids: Set[UUID] = set()
        to_visit: List[UUID] = [parent_agency_id]
        
        while to_visit:
            current_id = to_visit.pop()
            result = await db.execute(
                select(Agency.id).where(Agency.parent_agency_id == current_id)
            )
            children = [row[0] for row in result.all()]
            
            for child_id in children:
                if child_id not in child_ids:
                    child_ids.add(child_id)
                    to_visit.append(child_id)
        
        return list(child_ids)
    else:
        # Get only direct children
        result = await db.execute(
            select(Agency.id).where(Agency.parent_agency_id == parent_agency_id)
        )
        return [row[0] for row in result.all()]


async def get_agency_hierarchy_ids(
    db: AsyncSession,
    agency_id: UUID,
    include_children: bool = True,
) -> List[UUID]:
    """
    Get all agency IDs in the hierarchy (including the agency itself and all children).
    
    Args:
        db: Database session
        agency_id: Agency ID
        include_children: If True, include all child agencies
    
    Returns:
        List of agency IDs in the hierarchy
    """
    hierarchy_ids = {agency_id}
    
    if include_children:
        child_ids = await get_child_agency_ids(db, agency_id, recursive=True)
        hierarchy_ids.update(child_ids)
    
    return list(hierarchy_ids)


async def get_parent_agency_chain(
    db: AsyncSession,
    agency_id: UUID,
) -> List[Agency]:
    """
    Get the chain of parent agencies for a given agency.
    
    Args:
        db: Database session
        agency_id: Agency ID
    
    Returns:
        List of agencies from the agency up to the root (excluding the agency itself)
    """
    chain: List[Agency] = []
    current_id = agency_id
    
    while True:
        result = await db.execute(
            select(Agency).where(Agency.id == current_id)
        )
        agency = result.scalar_one_or_none()
        
        if not agency or agency.parent_agency_id is None:
            break
        
        # Get parent
        parent_result = await db.execute(
            select(Agency).where(Agency.id == agency.parent_agency_id)
        )
        parent = parent_result.scalar_one_or_none()
        
        if not parent:
            break
        
        chain.append(parent)
        current_id = parent.id
    
    return chain


async def build_hierarchy_filter_condition(
    db: AsyncSession,
    user_agency_id: UUID,
    user_role: str,
    column,
):
    """
    Build a SQLAlchemy filter condition for agency hierarchy.
    
    Args:
        db: Database session
        user_agency_id: User's agency ID
        user_role: User's role
        column: SQLAlchemy column to filter (e.g., Agency.id, VehicleObservation.agency_id)
    
    Returns:
        SQLAlchemy filter condition
    """
    from app.db.base import UserRole
    from sqlalchemy import or_
    
    # Admins see everything
    if user_role == UserRole.ADMIN:
        return True  # No filter
    
    # Load user's agency
    agency = await get_agency_with_hierarchy(db, user_agency_id)
    
    if not agency:
        # If agency not found, only show user's agency
        return column == user_agency_id
    
    # Based on agency type, determine what to include
    if agency.type == AgencyType.REGIONAL:
        # Regional agencies see themselves and all child agencies
        hierarchy_ids = await get_agency_hierarchy_ids(db, user_agency_id, include_children=True)
        return column.in_(hierarchy_ids)
    
    elif agency.type == AgencyType.LOCAL:
        # Local agencies see only themselves
        return column == user_agency_id
    
    else:
        # Other types (e.g., SPECIAL) see only themselves
        return column == user_agency_id


async def is_user_in_agency_hierarchy(
    db: AsyncSession,
    user_agency_id: UUID,
    target_agency_id: UUID,
) -> bool:
    """
    Check if a user's agency hierarchy includes the target agency.
    
    Args:
        db: Database session
        user_agency_id: User's agency ID
        target_agency_id: Target agency ID
    
    Returns:
        True if target agency is in user's hierarchy
    """
    # Same agency
    if user_agency_id == target_agency_id:
        return True
    
    # Check if target is a child of user's agency
    hierarchy_ids = await get_agency_hierarchy_ids(db, user_agency_id, include_children=True)
    return target_agency_id in hierarchy_ids
