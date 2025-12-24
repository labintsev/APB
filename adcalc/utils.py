from .models import db, Organisation, Smi, Region, District, Broadcast
from flask import current_app


def calculate_cost(broadcast):
    try:
        # Get the broadcast details
        smi = Smi.query.get_or_404(broadcast.smi_id)
        district = District.query.get_or_404(broadcast.district_id)
        if not smi or not district or not district.population:
            return 0
            
        region = Region.query.get_or_404(district.region_id)
        if not region:
            return 0
            
        cost = (smi.rating / 100) * district.population * region.rating
        return cost
    except Exception as e:
        print(f"Error calculating cost: {e}")
        return 0  # Return 0 if calculation fails
    