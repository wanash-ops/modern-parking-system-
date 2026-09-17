class SlotAllocator:
    """
    DSA Logic for MMU Parking System:
    - Array/Grid representation for slots
    - Linear Search / Hash verification for slot availability
    """
    def __init__(self, total_slots=12):
        self.total_slots = total_slots

    @staticmethod
    def calculate_fee(minutes: float) -> int:
        """
        MMU Tier Pricing:
        - Up to 30 mins: Kshs. 0
        - Up to 2 hours (120 mins): Kshs. 50
        - Up to 4 hours (240 mins): Kshs. 100
        - Up to 6 hours (360 mins): Kshs. 300
        - Over 6 hours: Kshs. 500
        """
        if minutes <= 30:
            return 0
        elif minutes <= 120:
            return 50
        elif minutes <= 240:
            return 100
        elif minutes <= 360:
            return 300
        else:
            return 500