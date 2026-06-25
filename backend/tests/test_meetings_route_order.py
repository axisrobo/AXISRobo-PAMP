import pytest


meetings_module = pytest.importorskip("app.routers.shared_services.meetings")
router = meetings_module.router


def test_meeting_static_routes_precede_dynamic_meeting_route():
    route_paths = [route.path for route in router.routes]

    attendees_template_index = route_paths.index("/attendees-template")
    parse_attendees_index = route_paths.index("/parse-attendees")
    dynamic_meeting_index = route_paths.index("/{meetingNo}")

    assert attendees_template_index < dynamic_meeting_index
    assert parse_attendees_index < dynamic_meeting_index