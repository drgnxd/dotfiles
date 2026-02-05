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
