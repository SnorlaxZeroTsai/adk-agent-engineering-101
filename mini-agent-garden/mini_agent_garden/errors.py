"""Domain errors mapped to deterministic CLI failures."""


class GardenError(Exception):
    """Base error for an enforceable Garden contract failure."""


class UnknownBlueprintError(GardenError):
    pass


class ContractValidationError(GardenError):
    pass


class ProjectIntegrityError(GardenError):
    pass


class UpgradeReviewRequired(GardenError):
    pass
