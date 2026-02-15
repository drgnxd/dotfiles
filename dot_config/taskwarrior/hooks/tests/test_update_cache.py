import io
import json

import update_cache
from update_cache import Task, build_cache_contents, task_from_dict


def test_task_from_dict_valid() -> None:
    data = {
        "id": 12,
        "description": "Write tests",
        "status": "pending",
        "project": "ops",
        "tags": ["work", 123],
    }
    task = task_from_dict(data)
    assert task == Task(
        id=12,
        description="Write tests",
        status="pending",
        project="ops",
        tags=["work"],
    )


def test_task_from_dict_invalid() -> None:
    assert task_from_dict({"id": 0, "description": "", "status": "pending"}) is None
    assert task_from_dict({"description": "Missing id", "status": "pending"}) is None
    assert task_from_dict({"id": 1, "status": "pending"}) is None


def test_build_cache_contents() -> None:
    tasks = [
        Task(id=1, description="First", status="pending"),
        Task(id=2, description="Second", status="pending"),
    ]
    ids, descs = build_cache_contents(tasks)
    assert ids == "1\n2"
    assert descs == "1:First\n2:Second"


def test_parse_hook_json_stream_single_object() -> None:
    parsed = update_cache.parse_hook_json_stream(
        '{"id":1,"description":"Write tests","status":"pending"}'
    )
    assert parsed is not None
    assert len(parsed) == 1
    assert isinstance(parsed[0], dict)
    assert parsed[0]["id"] == 1


def test_parse_hook_json_stream_two_objects() -> None:
    parsed = update_cache.parse_hook_json_stream(
        '{"id":1,"description":"Old","status":"pending"}\n'
        '{"id":1,"description":"New","status":"pending"}\n'
    )
    assert parsed is not None
    assert len(parsed) == 2
    assert isinstance(parsed[1], dict)
    assert parsed[1]["description"] == "New"


def test_parse_hook_json_stream_invalid_returns_none() -> None:
    parsed = update_cache.parse_hook_json_stream('{"id":1}\nthis-is-not-json')
    assert parsed is None


def test_process_hook_input_outputs_last_json_object(monkeypatch, capsys) -> None:
    called = False

    def fake_update_cache() -> None:
        nonlocal called
        called = True

    monkeypatch.setattr(update_cache, "update_cache", fake_update_cache)
    monkeypatch.setattr(
        update_cache.sys,
        "stdin",
        io.StringIO(
            '{"id":1,"description":"Old","status":"pending"}\n'
            '{"id":1,"description":"New","status":"pending"}\n'
        ),
    )

    update_cache.process_hook_input()

    captured = capsys.readouterr()
    output_payload = json.loads(captured.out)
    assert output_payload["description"] == "New"
    assert called is True


def test_process_hook_input_falls_back_to_last_nonempty_line(
    monkeypatch, capsys
) -> None:
    called = False

    def fake_update_cache() -> None:
        nonlocal called
        called = True

    monkeypatch.setattr(update_cache, "update_cache", fake_update_cache)
    monkeypatch.setattr(update_cache, "log_hook_error", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        update_cache.sys,
        "stdin",
        io.StringIO('not-json\n{"id":2,"description":"Task","status":"pending"}\n'),
    )

    update_cache.process_hook_input()

    captured = capsys.readouterr()
    assert captured.out.strip() == '{"id":2,"description":"Task","status":"pending"}'
    assert called is True


def test_process_hook_input_empty_stdin(monkeypatch, capsys) -> None:
    called = False

    def fake_update_cache() -> None:
        nonlocal called
        called = True

    monkeypatch.setattr(update_cache, "update_cache", fake_update_cache)
    monkeypatch.setattr(update_cache.sys, "stdin", io.StringIO("\n   \n"))

    update_cache.process_hook_input()

    captured = capsys.readouterr()
    assert captured.out == ""
    assert called is True
