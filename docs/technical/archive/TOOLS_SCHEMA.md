<!--
Input: 当前技术架构、模块边界与工程约束。
Output: 输出技术文档《Tools Schema - Resume Fit Agent》的说明内容。
Pos: 技术设计文档。
Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
-->
# Tools Schema - Resume Fit Agent

All tools use strict JSON I/O. The core agent enforces schema validation.

---

## Common Context Envelope

All tool inputs include runtime context:

```json
{
  "project_id": "string",
  "message_id": "string",
  "user_id": "string",
  "task_card_id": "string"
}
```

`task_card_id` can be empty for project-level events like `ingest_jd`.

---

## 0. input_router

### Input
```json
{
  "message_text": "string",
  "attachments": [
    {
      "type": "resume|jd|other",
      "content": "string"
    }
  ]
}
```

### Output
```json
{
  "jd_count_hint": 0,
  "events": [
    {
      "event_type": "resume_update|ingest_jd|profile_supplement|command",
      "routed_intent": "update_resume|ingest_jd|add_info|generate|compare|abandon",
      "payload_ref": "string",
      "scope": "project|task_card",
      "source_task_card_id": "string"
    }
  ],
  "should_split_jd": true
}
```

---

## 1. jd_parser

### Input
```json
{
  "jd_text": "string",
  "source": "text|ocr"
}
```

### Output
```json
{
  "jd_count": 0,
  "jd_entries": [
    {
      "project_jd_id": "string",
      "title": "string",
      "raw_text_ref": "string"
    }
  ],
  "direction_count": 0,
  "resume_output_count": 0,
  "directions": [
    {
      "direction_id": "string",
      "direction_name": "string",
      "source_jd_ids": ["string"],
      "keywords": ["string"],
      "capabilities": [
        {
          "tag": "string",
          "weight": 0.0,
          "evidence": "string"
        }
      ],
      "summary": "string"
    }
  ],
  "split_preview": [
    {
      "jd_id": "string",
      "title": "string",
      "mapped_direction_id": "string"
    }
  ]
}
```

---

## 1.5 project_jd_allocator

Routes project-owned JD entries to task cards.

### Input
```json
{
  "source_scope": "project|task_card",
  "source_task_card_id": "string",
  "jd_entries": [
    {
      "project_jd_id": "string",
      "mapped_direction_id": "string"
    }
  ],
  "existing_task_cards": [
    {
      "task_card_id": "string",
      "direction_id": "string",
      "direction_name": "string"
    }
  ],
  "require_preview_confirm": true
}
```

### Output
```json
{
  "need_user_confirm": true,
  "preview": {
    "jd_count": 0,
    "direction_count": 0,
    "proposed_task_card_changes": [
      {
        "action": "assign_current_card|assign_existing_card|create_new_card",
        "project_jd_id": "string",
        "target_task_card_id": "string",
        "target_direction_name": "string",
        "reason": "string"
      }
    ]
  },
  "allocations": [
    {
      "project_jd_id": "string",
      "decision": "assign_current_card|assign_existing_card|create_new_card",
      "target_task_card_id": "string",
      "reason": "string"
    }
  ]
}
```

---

## 2. resume_parser

### Input
```json
{
  "resume_text": "string",
  "format": "text|pdf"
}
```

### Output
```json
{
  "experiences": [
    {
      "title": "string",
      "time": "string",
      "summary": "string",
      "evidence_spans": ["string"]
    }
  ],
  "skills": ["string"],
  "profile_facts": {
    "education": ["string"],
    "constraints": ["string"]
  }
}
```

---

## 3. scorer

### Input
```json
{
  "direction_id": "string",
  "jd": {
    "capabilities": []
  },
  "resume": {
    "experiences": []
  },
  "supplements": [
    {
      "field": "string",
      "value": "string"
    }
  ]
}
```

### Output
```json
{
  "direction_id": "string",
  "score_total": 0,
  "score_fit": 0,
  "score_risk": 0,
  "score_recall": 0,
  "match_level": "high|medium|low",
  "rationale": "string",
  "missing_slots": ["string"]
}
```

---

## 4. improver

### Input
```json
{
  "direction_id": "string",
  "resume": {
    "experiences": []
  },
  "jd": {
    "capabilities": []
  },
  "supplements": [
    {
      "field": "string",
      "value": "string"
    }
  ],
  "constraints": {
    "no_fabrication": true
  }
}
```

### Output
```json
{
  "direction_id": "string",
  "resume_revised": "string",
  "change_log": [
    {
      "from": "string",
      "to": "string",
      "reason": "string",
      "evidence": "string"
    }
  ]
}
```

---

## 5. reviewer

### Input
```json
{
  "direction_id": "string",
  "resume_before": "string",
  "resume_after": "string",
  "jd": {
    "capabilities": []
  }
}
```

### Output
```json
{
  "direction_id": "string",
  "score_before": 0,
  "score_after": 0,
  "pass": true,
  "guidance": "string",
  "next_action": "deliver|supplement|risk_confirm|abandon"
}
```

---

## 6. task_state_manager

This can be implemented as an internal core service instead of an external tool.

### Input
```json
{
  "project_id": "string",
  "event_type": "resume_update|ingest_jd|jd_allocated|profile_supplement|review_done",
  "target_task_card_ids": ["string"],
  "payload": {}
}
```

### Output
```json
{
  "task_updates": [
    {
      "task_card_id": "string",
      "status": "pending|scored|generating|completed|abandoned",
      "match_level": "high|medium|low",
      "mode": "normal|compensation"
    }
  ],
  "project_summary": {
    "jd_count": 0,
    "direction_count": 0,
    "resume_output_count": 0
  }
}
```
