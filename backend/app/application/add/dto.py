from dataclasses import dataclass


@dataclass
class ConcernDTO:
    code: str
    name: str
    category: str
    description: str = ""
    severity: str = "medium"
    likelihood: str = "medium"
    classification: str = "recommended"


@dataclass
class AssessmentDTO:
    project_id: str
    concern_id: str
    score: int = 0
    notes: str = ""
    assessed_by: str = ""


@dataclass
class AssessmentResultDTO:
    concern_code: str
    concern_name: str
    score: int
    classification: str
    recommendation: str
