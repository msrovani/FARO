"""
Materialized Views Management for FARO.
Functions to refresh materialized views for hotspots analysis.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


async def refresh_materialized_views(db: AsyncSession) -> None:
    """
    Refresh all materialized views for hotspots analysis.
    Should be called periodically (e.g., every hour) to keep data fresh.
    Uses CONCURRENTLY to avoid blocking writes.
    
    Args:
        db: AsyncSession database session
    """
    try:
        # Refresh daily hotspots
        await db.execute(
            text("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_hotspots;")
        )
        
        # Refresh agency hotspots
        await db.execute(
            text("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_agency_hotspots;")
        )
        
        await db.commit()
        print("Materialized views refreshed successfully")
    except Exception as e:
        await db.rollback()
        print(f"Failed to refresh materialized views: {e}")
        raise


async def get_daily_hotspots(
    db: AsyncSession,
    days: int = 7,
    agency_id: str = None
) -> list[dict]:
    """
    Get hotspot data from materialized view.
    
    Args:
        db: AsyncSession database session
        days: Number of days of data to retrieve
        agency_id: Optional agency_id filter (None for all agencies)
    
    Returns:
        List of hotspot data dictionaries
    """
    if agency_id:
        query = text("""
            SELECT * FROM mv_agency_hotspots
            WHERE agency_id = :agency_id
            AND observation_date >= CURRENT_DATE - INTERVAL ':days days'
            ORDER BY observation_date DESC
        """)
        result = await db.execute(query, {"agency_id": agency_id, "days": days})
    else:
        query = text("""
            SELECT * FROM mv_daily_hotspots
            WHERE observation_date >= CURRENT_DATE - INTERVAL ':days days'
            ORDER BY observation_date DESC
        """)
        result = await db.execute(query, {"days": days})
    
    return [dict(row._mapping) for row in result]
