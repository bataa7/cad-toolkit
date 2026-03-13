from notification_system import NotificationWidget


def test_notification_widget_detects_only_new_ids():
    previous = [
        {"id": "n1", "title": "First"},
    ]
    current = [
        {"id": "n1", "title": "First"},
        {"id": "n2", "title": "Second"},
    ]

    result = NotificationWidget._find_new_unread_notifications(previous, current)

    assert [item["id"] for item in result] == ["n2"]


def test_notification_widget_excludes_read_ids():
    previous = [
        {"id": "n1", "title": "First"},
    ]
    current = [
        {"id": "n1", "title": "First"},
        {"id": "n2", "title": "Second"},
        {"id": "n3", "title": "Third"},
    ]

    result = NotificationWidget._find_new_unread_notifications(previous, current, {"n3"})

    assert [item["id"] for item in result] == ["n2"]
