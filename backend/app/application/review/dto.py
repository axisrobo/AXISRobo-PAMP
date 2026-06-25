from dataclasses import dataclass

@dataclass
class ReviewRequestDTO:
    request_id: str
    title: str
    description: str = ""
    submitter: str = ""
    reviewer: str = ""
