#!/usr/bin/env python3
"""Ed formatting tests: authors, thread types, accepted answers, nested replies, attachments.

Run directly: python3 test_ed_format.py
Fixtures mirror the shape of real GET /api/threads/<id> responses (thread + users).
"""
import canvas_ed_mcp as m

USERS = [
    {"id": 1, "name": "Student One", "course_role": "student"},
    {"id": 2, "name": "Tutor Two", "course_role": "admin"},
]

THREAD = {
    "id": 100,
    "title": "How do I plot?",
    "type": "question",
    "is_answered": True,
    "category": "Assignments",
    "subcategory": "A2",
    "user_id": 1,
    "is_anonymous": False,
    "accepted_id": 201,
    "created_at": "2026-10-13T07:13:00+11:00",
    "document": "See attached spec.",
    "content": '<document version="2.0"><paragraph>See attached spec.</paragraph>'
               '<file url="https://static.example/files/abc" filename="Spec &amp; Rubric.pdf"/>'
               '<image src="https://static.example/files/img1" width="100"/></document>',
    "answers": [
        {"id": 201, "user_id": 2, "document": "Use matplotlib.", "content": "", "comments": [
            {"id": 301, "user_id": 1, "document": "Thanks!", "content": "", "comments": [
                {"id": 401, "user_id": 2, "is_endorsed": True, "document": "No worries.",
                 "content": "", "comments": []},
            ]},
        ]},
    ],
    "comments": [
        {"id": 202, "user_id": 1, "is_anonymous": True, "document": "Same question", "content": "",
         "comments": []},
    ],
}

out = m.format_ed_thread_detail_markdown(THREAD, USERS)

# Thread metadata comes from `type` and the users list, not `is_question` / `user`
assert "**Type**: Question (Answered)" in out, out
assert "**Category**: Assignments / A2" in out, out
assert "**Author**: Student One" in out, out

# Attachments are read from the XML `content` (the plain-text `document` drops them)
assert "[Spec & Rubric.pdf](https://static.example/files/abc)" in out, out
assert "[image](https://static.example/files/img1)" in out, out

# Accepted answer is matched via the thread's accepted_id; staff role is shown
assert "### 1. Tutor Two (admin) ✅ Accepted Answer" in out, out

# Nested replies are rendered at every depth instead of being dropped
assert "#### 1.1. Student One" in out, out
assert "##### 1.1.1. Tutor Two (admin) 👍 Endorsed" in out, out
assert "No worries." in out, out

# Anonymous replies stay anonymous even when user_id resolves to a real user
assert "### 1. Anonymous" in out, out

# Thread list: type label and reply_count come from the real field names
listing = m.format_ed_threads_markdown([
    {"id": 1, "title": "A2 helpdesk", "type": "announcement", "reply_count": 4,
     "user": {"name": "Tutor Two"}},
    {"id": 2, "title": "Bug?", "type": "question", "is_answered": False, "reply_count": 0},
])
assert "## 1. [Announcement] A2 helpdesk" in listing, listing
assert "**Replies**: 4" in listing, listing
assert "## 2. [Question] Bug? ❓ Unanswered" in listing, listing

# Attachment extraction tolerates empty or attachment-free content
assert m.extract_ed_attachments("") == []
assert m.extract_ed_attachments("<document><paragraph>hi</paragraph></document>") == []

print("all ed format tests passed")
