from typing import Literal


Priority = Literal["ignore", "low", "medium", "high", "must-see"]
PlanningType = Literal["standalone", "package", "package_member"]
SelectionStatus = Literal["none", "tentative", "confirmed", "rejected"]
