from app.domain.add.entities import Concern, ProjectAssessment, Viewpoint, Artifact


def test_concern_creation():
    concern = Concern(code="C001", name="Security Review", category="security", severity="high")
    assert concern.code == "C001"
    assert concern.severity == "high"
    assert concern.likelihood == "medium"


def test_project_assessment_defaults():
    assessment = ProjectAssessment(project_id="proj-1", concern_id="C001")
    assert assessment.score == 0
    assert assessment.notes == ""


def test_viewpoint_creation():
    vp = Viewpoint(code="SEC", name="Security Viewpoint", description="Security architecture concerns")
    assert vp.code == "SEC"
    assert vp.description == "Security architecture concerns"


def test_artifact_creation():
    art = Artifact(code="ART-01", name="Threat Model", viewpoint_code="SEC")
    assert art.viewpoint_code == "SEC"
    assert art.description == ""
