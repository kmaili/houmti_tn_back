class ServiceItemCantBeDeletedException(Exception):
    def __init__(self, message="This service item cannot be deleted because it has a non-completed booking."):
        self.message = message
        super().__init__(self.message)