from cn_linux_cu_demo.action_parser import parse_actions
from cn_linux_cu_demo.schemas import ActionKind


def test_parse_json_tool_call_left_click() -> None:
    actions = parse_actions(
        'Action: click\n<tool_call>{"name":"computer","arguments":{"action":"left_click","coordinate":[250,500]}}</tool_call>'
    )
    assert actions[0].kind == ActionKind.LEFT_CLICK
    assert actions[0].coordinate.x == 250
    assert actions[0].coordinate.y == 500


def test_parse_qwen_xml_hotkey() -> None:
    actions = parse_actions(
        "Action: save\n"
        "<tool_call><function=computer_use>"
        "<parameter=action>key</parameter>"
        "<parameter=keys>[\"ctrl\", \"s\"]</parameter>"
        "</function></tool_call>"
    )
    assert actions[0].kind == ActionKind.KEY
    assert actions[0].keys == ["ctrl", "s"]


def test_parse_terminate_failure() -> None:
    actions = parse_actions(
        '<tool_call>{"name":"computer","arguments":{"action":"terminate","status":"failure"}}</tool_call>'
    )
    assert actions[0].kind == ActionKind.FAIL


def test_infeasible_maps_to_fail() -> None:
    actions = parse_actions("[INFEASIBLE]")
    assert actions[0].kind == ActionKind.FAIL
