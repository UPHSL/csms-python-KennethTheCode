from dataclasses import dataclass

from csms.models.resident import Resident


@dataclass
class ResidentDeactivationResult:
    success: bool
    resident: Resident | None = None
    already_inactive: bool = False
    not_found: bool = False

    @classmethod
    def deactivated(cls, resident: Resident) -> "ResidentDeactivationResult":
        return cls(success=True, resident=resident)

    @classmethod
    def was_already_inactive(
        cls, resident: Resident
    ) -> "ResidentDeactivationResult":
        return cls(success=True, resident=resident, already_inactive=True)

    @classmethod
    def resident_not_found(cls) -> "ResidentDeactivationResult":
        return cls(success=False, not_found=True)