from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional


SENSITIVE_PATTERNS = (
    "парол",
    "токен",
    "secret",
    "ключ доступа",
    "api key",
    "2fa",
    "otp",
    "код подтверждения",
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def channel_key(guild_id: Any, channel_id: Any) -> str:
    return f"{guild_id}:{channel_id}"


def ensure_memory_schema(data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    payload: Dict[str, Any] = dict(data or {})
    payload.setdefault("memory", {})
    payload.setdefault("summary", {})
    payload.setdefault("raw_history", {})
    payload.setdefault("channel_history", {})
    payload.setdefault("personas", {})
    payload.setdefault("known_members", {})
    return payload


def load_json(path: str, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if not os.path.exists(path):
        return dict(default or {})
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def save_json(path: str, data: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=4)


def _append_limited(items: list, value: Dict[str, Any], limit: int) -> None:
    items.append(value)
    if len(items) > limit:
        del items[:-limit]


def append_channel_message(
    data: Dict[str, Any],
    *,
    guild_id: Any,
    channel_id: Any,
    message_id: Optional[Any] = None,
    author_id: Any,
    author_name: str,
    content: str,
    role: str,
    timestamp: Optional[str] = None,
    limit: int = 120,
) -> Dict[str, Any]:
    payload = ensure_memory_schema(data)
    history = payload["channel_history"].setdefault(channel_key(guild_id, channel_id), [])
    entry = {
        "guild_id": str(guild_id),
        "channel_id": str(channel_id),
        "message_id": str(message_id) if message_id is not None else None,
        "author_id": str(author_id),
        "author_name": author_name,
        "role": role,
        "content": content,
        "timestamp": timestamp or utc_now_iso(),
    }
    _append_limited(history, entry, limit)
    return entry


def append_user_message(
    data: Dict[str, Any],
    *,
    user_id: Any,
    username: str,
    message_id: Optional[Any] = None,
    content: str,
    role: str,
    timestamp: Optional[str] = None,
    limit: int = 50,
) -> Dict[str, Any]:
    payload = ensure_memory_schema(data)
    user_bucket = payload["memory"].setdefault(str(user_id), {})
    user_bucket.setdefault("username", username)
    user_bucket.setdefault("knowledge", {})
    user_bucket.setdefault("messages", [])
    entry = {
        "type": role,
        "message_id": str(message_id) if message_id is not None else None,
        "content": content,
        "timestamp": timestamp or utc_now_iso(),
        "username": username,
    }
    _append_limited(user_bucket["messages"], entry, limit)
    raw_history = payload["raw_history"].setdefault(str(user_id), [])
    _append_limited(raw_history, entry.copy(), limit)
    return entry


def render_channel_history(
    data: Dict[str, Any],
    *,
    guild_id: Any,
    channel_id: Any,
    exclude_message_id: Optional[Any] = None,
    limit: int = 10,
) -> str:
    payload = ensure_memory_schema(data)
    history = payload["channel_history"].get(channel_key(guild_id, channel_id), [])
    if not history:
        return ""
    exclude_message_id = str(exclude_message_id) if exclude_message_id is not None else None
    parts = []
    for item in history[-limit:]:
        if exclude_message_id is not None and str(item.get("message_id")) == exclude_message_id:
            continue
        author = item.get("author_name") or item.get("author_id") or "unknown"
        content = item.get("content", "")
        message_id = item.get("message_id")
        prefix = f"[message_id={message_id}] " if message_id else ""
        parts.append(f"{prefix}{author}: {content}")
    return "\n".join(parts)


def render_user_history(
    data: Dict[str, Any],
    user_id: Any,
    limit: int = 5,
    exclude_message_id: Optional[Any] = None,
) -> str:
    payload = ensure_memory_schema(data)
    history = payload["raw_history"].get(str(user_id), [])
    if not history:
        return ""
    exclude_message_id = str(exclude_message_id) if exclude_message_id is not None else None
    parts = []
    for item in history[-limit:]:
        if isinstance(item, dict):
            if exclude_message_id is not None and str(item.get("message_id")) == exclude_message_id:
                continue
            role = item.get("type", "user")
            content = item.get("content", "")
            parts.append(f"{role}: {content}")
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            parts.append(f"{item[0]}: {item[1]}")
        else:
            parts.append(str(item))
    return "\n".join(parts)


def summarize_memory_facts(data: Dict[str, Any], user_id: Any) -> str:
    payload = ensure_memory_schema(data)
    user_bucket = payload["memory"].get(str(user_id), {})
    knowledge = user_bucket.get("knowledge", {})
    if not knowledge:
        return ""
    facts = []
    for key, value in knowledge.items():
        if isinstance(value, dict):
            explanation = value.get("explanation")
            if explanation:
                facts.append(f"• {key}: {explanation}")
            else:
                facts.append(f"• {key}: {value}")
        else:
            facts.append(f"• {key}: {value}")
    return "\n".join(facts)


def _normalize_fact_text(value: str) -> str:
    value = re.sub(r"\s+", " ", value).strip(" ,.;:-")
    return value


def _extract_fact_value(patterns: Iterable[str], text: str) -> Optional[str]:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        if match:
            value = _normalize_fact_text(match.group(1))
            if value:
                return value
    return None


def extract_memory_facts(content: str) -> list[Dict[str, str]]:
    text = (content or "").strip()
    if not text:
        return []

    lowered = text.lower()
    if any(marker in lowered for marker in SENSITIVE_PATTERNS):
        return []

    facts: list[Dict[str, str]] = []

    name = _extract_fact_value(
        (
            r"(?:меня зовут|мо[её] имя|мой ник)\s+([A-Za-zА-Яа-я0-9_\- ]{2,40})",
            r"(?:я\s+это|я\s+—)\s+([A-Za-zА-Яа-я0-9_\- ]{2,40})",
        ),
        text,
    )
    if name:
        facts.append(
            {
                "key": "name",
                "value": name,
                "explanation": f"Пользователь представился как {name}",
            }
        )

    interests = _extract_fact_value(
        (
            r"(?:я люблю|мне нравится|я обожаю)\s+([^.!?]{2,80})",
        ),
        text,
    )
    if interests:
        facts.append(
            {
                "key": "interests",
                "value": interests,
                "explanation": f"Пользователю нравится {interests}",
            }
        )

    occupation = _extract_fact_value(
        (
            r"(?:я работаю(?:\s+как|\s+в)?|я\s+профессией\s+являюсь)\s+([^.!?]{2,80})",
            r"(?:я\s+(?:программист|разработчик|тестировщик|дизайнер|аналитик|менеджер|студент|ученик))\b([^.!?]{0,40})",
            r"(?:я учусь(?:\s+на|\s+в)?)\s+([^.!?]{2,80})",
        ),
        text,
    )
    if occupation:
        facts.append(
            {
                "key": "occupation",
                "value": occupation,
                "explanation": f"Пользователь сообщил о занятости: {occupation}",
            }
        )

    location = _extract_fact_value(
        (
            r"(?:я из|живу в|нахожусь в)\s+([^.!?]{2,80})",
        ),
        text,
    )
    if location:
        facts.append(
            {
                "key": "location",
                "value": location,
                "explanation": f"Пользователь связан с локацией {location}",
            }
        )

    return facts


def _merge_fact_record(existing: Any, fact: Dict[str, str]) -> Dict[str, Any]:
    record = {
        "value": fact["value"],
        "explanation": fact["explanation"],
        "source_message": fact.get("source_message", ""),
        "updated_at": fact.get("timestamp", utc_now_iso()),
    }
    if isinstance(existing, dict):
        previous_value = existing.get("value")
        if previous_value and previous_value != fact["value"]:
            if isinstance(previous_value, list):
                merged_values = list(previous_value)
            else:
                merged_values = [str(previous_value)]
            if fact["value"] not in merged_values:
                merged_values.append(fact["value"])
            record["value"] = merged_values
            record["explanation"] = fact["explanation"]
        else:
            record["value"] = previous_value or fact["value"]
            record["explanation"] = existing.get("explanation") or fact["explanation"]
            record["source_message"] = existing.get("source_message", fact.get("source_message", ""))
    return record


def remember_user_facts(
    data: Dict[str, Any],
    *,
    user_id: Any,
    username: str,
    content: str,
    source_message: Optional[str] = None,
    timestamp: Optional[str] = None,
) -> list[Dict[str, Any]]:
    payload = ensure_memory_schema(data)
    facts = extract_memory_facts(content)
    if not facts:
        return []

    user_bucket = payload["memory"].setdefault(str(user_id), {})
    user_bucket.setdefault("username", username)
    user_bucket.setdefault("knowledge", {})
    saved: list[Dict[str, Any]] = []
    for fact in facts:
        fact_copy = dict(fact)
        fact_copy["source_message"] = source_message or content
        fact_copy["timestamp"] = timestamp or utc_now_iso()
        existing = user_bucket["knowledge"].get(fact["key"])
        record = _merge_fact_record(existing, fact_copy)
        user_bucket["knowledge"][fact["key"]] = record
        saved.append({"key": fact["key"], **record})
    return saved


def upsert_known_member(data: Dict[str, Any], *, guild_id: Any, member: Any) -> Dict[str, Any]:
    payload = ensure_memory_schema(data)
    guild_bucket = payload["known_members"].setdefault(str(guild_id), {})
    record = {
        "member_id": str(getattr(member, "id", "")),
        "username": getattr(member, "name", ""),
        "display_name": getattr(member, "display_name", getattr(member, "name", "")),
        "mention": getattr(member, "mention", f"<@{getattr(member, 'id', '')}>"),
        "last_seen": utc_now_iso(),
    }
    guild_bucket[str(getattr(member, "id", ""))] = record
    return record


def _score_member(member: Any, query: str) -> int:
    query_norm = normalize_lookup_text(query)
    if not query_norm:
        return 0
    candidates = [
        str(getattr(member, "id", "")),
        normalize_lookup_text(getattr(member, "name", "")),
        normalize_lookup_text(getattr(member, "display_name", "")),
        normalize_lookup_text(getattr(member, "global_name", "")),
    ]
    score = 0
    for candidate in candidates:
        if not candidate:
            continue
        if candidate == query_norm:
            score = max(score, 100)
        elif candidate.startswith(query_norm):
            score = max(score, 80)
        elif query_norm in candidate:
            score = max(score, 60)
    return score


def normalize_lookup_text(value: Any) -> str:
    text = str(value or "").lower()
    text = re.sub(r"<[@#&!]?\d+>", " ", text)
    text = re.sub(r"[_\-|/\\:;.,()\[\]{}\"'`~+*=]+", " ", text)
    text = "".join(ch if ch.isalnum() or ch.isspace() else " " for ch in text)
    return re.sub(r"\s+", " ", text).strip()


def _score_lookup(candidate: Any, query: Any) -> int:
    query_norm = normalize_lookup_text(query)
    candidate_norm = normalize_lookup_text(candidate)
    if not query_norm or not candidate_norm:
        return 0
    if candidate_norm == query_norm:
        return 100
    if candidate_norm.startswith(query_norm):
        return 85
    if query_norm in candidate_norm:
        return 75
    query_tokens = set(query_norm.split())
    candidate_tokens = set(candidate_norm.split())
    if query_tokens and query_tokens.issubset(candidate_tokens):
        return 80
    if query_tokens & candidate_tokens:
        return 45
    return 0


def resolve_member(guild: Any, query: str) -> Optional[Any]:
    if guild is None or not query:
        return None
    q = query.strip()
    if not q:
        return None
    mention = re.fullmatch(r"<@!?(\d+)>", q)
    if mention:
        q = mention.group(1)
    members: Iterable[Any] = getattr(guild, "members", []) or []
    best = None
    best_score = -1
    for member in members:
        if str(getattr(member, "id", "")) == q:
            return member
        score = _score_member(member, q)
        if score > best_score:
            best = member
            best_score = score
    return best if best_score > 0 else None


def find_known_member(data: Dict[str, Any], *, guild_id: Any, query: str) -> Optional[Dict[str, Any]]:
    payload = ensure_memory_schema(data)
    guild_bucket = payload["known_members"].get(str(guild_id), {})
    q = query.strip().lower()
    if not q:
        return None
    if q in guild_bucket:
        return guild_bucket[q]
    for member_id, record in guild_bucket.items():
        values = [
            member_id,
            str(record.get("username", "")).lower(),
            str(record.get("display_name", "")).lower(),
        ]
        if q in values or any(v.startswith(q) for v in values if v):
            return record
    return None


def format_member_mention(member: Any) -> str:
    mention = getattr(member, "mention", None)
    if mention:
        return mention
    return f"<@{getattr(member, 'id', '')}>"


def resolve_text_channel(guild: Any, query: str) -> Optional[Any]:
    if guild is None or not query:
        return None
    q = query.strip().lower()
    channel_id = re.fullmatch(r"<#(\d+)>", query.strip())
    if channel_id:
        q = channel_id.group(1)
    channels: Iterable[Any] = getattr(guild, "text_channels", []) or []
    best = None
    best_score = -1
    for channel in channels:
        if str(getattr(channel, "id", "")) == q:
            return channel
        name = str(getattr(channel, "name", ""))
        if name.lower() == q:
            return channel
        score = _score_lookup(name, query)
        if score > best_score:
            best = channel
            best_score = score
    return best if best_score > 0 else None


def resolve_role(guild: Any, query: str) -> Optional[Any]:
    if guild is None or not query:
        return None
    q = query.strip()
    mention = re.fullmatch(r"<@&(\d+)>", q)
    if mention:
        q = mention.group(1)
    roles: Iterable[Any] = getattr(guild, "roles", []) or []
    best = None
    best_score = -1
    for role in roles:
        if str(getattr(role, "id", "")) == q:
            return role
        score = _score_lookup(getattr(role, "name", ""), q)
        if score > best_score:
            best = role
            best_score = score
    return best if best_score > 0 else None


def can_post_to_channel(channel: Any, allowed_channel_ids: Optional[Iterable[str]] = None) -> bool:
    if channel is None:
        return False
    if allowed_channel_ids is None:
        return True
    channel_id = str(getattr(channel, "id", ""))
    return channel_id in {str(item) for item in allowed_channel_ids}


def bot_channel_permissions(channel: Any, bot_member: Any) -> Any:
    if channel is None or bot_member is None or not hasattr(channel, "permissions_for"):
        return None
    return channel.permissions_for(bot_member)


def can_bot_send(channel: Any, bot_member: Any) -> bool:
    permissions = bot_channel_permissions(channel, bot_member)
    if permissions is None:
        return False
    return bool(
        getattr(permissions, "view_channel", False)
        and getattr(permissions, "send_messages", False)
    )


def can_bot_react(channel: Any, bot_member: Any) -> bool:
    permissions = bot_channel_permissions(channel, bot_member)
    if permissions is None:
        return False
    return bool(
        getattr(permissions, "view_channel", False)
        and getattr(permissions, "read_message_history", False)
        and getattr(permissions, "add_reactions", False)
    )


def get_online_members(guild: Any, include_bots: bool = False) -> list[Any]:
    members = getattr(guild, "members", []) or []
    result = []
    for member in members:
        if not include_bots and getattr(member, "bot", False):
            continue
        status = str(getattr(member, "status", "offline")).lower()
        if status not in ("offline", "invisible"):
            result.append(member)
    return result


def is_ping_summary_request(content: str) -> bool:
    text = (content or "").lower()
    return any(
        phrase in text
        for phrase in (
            "кого пинганул",
            "кого пинганула",
            "кто пинганул",
            "кто пинганула",
            "кого я пинганул",
            "кого я пинганула",
            "кто я пинганул",
            "кто я пинганула",
            "кого я упомянул",
            "кого я упомянула",
            "кого упомянул",
            "кого упомянула",
            "кто упомянул",
            "кто упомянула",
            "кого я пинговал",
            "кого пинговал",
            "кого я позвал",
            "кого позвал",
            "кто у меня в пинге",
        )
    )


def _format_display_member(member: Any) -> str:
    display_name = getattr(member, "display_name", "") or getattr(member, "name", "")
    member_id = getattr(member, "id", None)
    if display_name and member_id is not None:
        return f"{display_name} (ID {member_id})"
    if display_name:
        return display_name
    if member_id is not None:
        return f"ID {member_id}"
    return "неизвестный участник"


def summarize_message_mentions(message: Any, bot_user: Any = None) -> Optional[str]:
    content = getattr(message, "content", "") or ""
    if not is_ping_summary_request(content):
        return None

    bot_id = getattr(bot_user, "id", None)
    mentions = list(getattr(message, "mentions", []) or [])
    raw_mentions = list(getattr(message, "raw_mentions", []) or [])
    mention_ids = {str(getattr(member, "id", "")) for member in mentions if getattr(member, "id", None) is not None}
    mention_map = {str(getattr(member, "id", "")): member for member in mentions if getattr(member, "id", None) is not None}

    if not mention_ids and raw_mentions:
        guild = getattr(message, "guild", None)
        for raw_id in raw_mentions:
            member = None
            if guild is not None and hasattr(guild, "get_member"):
                try:
                    member = guild.get_member(int(raw_id))
                except Exception:
                    member = None
            if member is not None:
                mention_map[str(raw_id)] = member
            else:
                mention_map[str(raw_id)] = raw_id

    human_mentions = []
    bot_mentioned = False
    for key, member in mention_map.items():
        if bot_id is not None and str(key) == str(bot_id):
            bot_mentioned = True
            continue
        human_mentions.append(member)

    if human_mentions and bot_mentioned:
        names = ", ".join(_format_display_member(member) for member in human_mentions)
        return f"Ты пинганул: {names} и меня."
    if human_mentions:
        names = ", ".join(_format_display_member(member) for member in human_mentions)
        return f"Ты пинганул: {names}."
    if bot_mentioned:
        return "Ты пинганул меня."
    return "Ты никого не пинганул."
