from .models import db, Region, Broadcast
from flask import current_app


def calculate_cost(broadcast):
    try:
        # Use embedded fields on Broadcast (smi_rating and district_population)
        if not broadcast or not broadcast.smi_rating or not broadcast.district_population:
            return 0

        # Prefer the Region object attached via relationship when available
        region = getattr(broadcast, 'region', None)
        if not region:
            region = Region.query.get(broadcast.region_id)
        if not region or not region.rating:
            return 0

        cost = (broadcast.smi_rating / 100.0) * broadcast.district_population * region.rating
        return cost
    except Exception as e:
        print(f"Error calculating cost: {e}")
        return 0
    