from dataclasses import dataclass

@dataclass
class ProjectDTO:
    name: str
    description: str = ""
    status: str = "active"
    owner_id: str = ""
    category: str = "regular"
    type: str = ""
    start_date: str = ""
    go_live_date: str = ""
    duration: str = ""
    objectives: str = ""
    ai_related: str = ""
    comment: str = ""
    pm: str = ""
    pm_itcode: str = ""
    dt_lead: str = ""
    dt_lead_itcode: str = ""
    it_lead: str = ""
    it_lead_itcode: str = ""

@dataclass
class TeamMemberDTO:
    project_id: str
    user_itcode: str
    role: str = "member"
