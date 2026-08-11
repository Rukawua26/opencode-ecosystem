import { createHash } from "node:crypto";

const CONTENT_FIELDS = {
  decision: ["category", "title", "content", "rationale"],
  bugfix: ["title", "description", "root_cause", "fix", "lesson"],
  architecture: ["component", "description", "rationale"],
  preference: ["key", "value"],
  operational: ["session_id", "action", "detail", "result", "files_touched"],
};

function canonicalValue(value) {
  if (Array.isArray(value)) return value.map(canonicalValue);
  if (!value || typeof value !== "object") return value;
  return Object.fromEntries(
    Object.keys(value).sort().map((key) => [key, canonicalValue(value[key])]),
  );
}

export function canonicalJson(value) {
  return JSON.stringify(canonicalValue(value));
}

function parseTag(tag) {
  if (Array.isArray(tag)) return tag.map(String);
  const text = String(tag).trim();
  if (!text) return null;
  const separator = text.indexOf(":");
  return separator > 0
    ? [text.slice(0, separator).trim(), text.slice(separator + 1).trim()]
    : ["tag", text];
}

export function normalizeEventTags(tags, references = {}) {
  let values = [];
  if (Array.isArray(tags)) {
    values = tags;
  } else if (typeof tags === "string" && tags.trim()) {
    try {
      const parsed = JSON.parse(tags);
      values = Array.isArray(parsed) ? parsed : [tags];
    } catch {
      values = tags.split(",");
    }
  }

  const normalized = values.map(parseTag).filter(Boolean);
  for (const [name, rawValue] of Object.entries(references || {})) {
    for (const value of Array.isArray(rawValue) ? rawValue : [rawValue]) {
      if (value !== undefined && value !== null && String(value).trim()) {
        normalized.push([name, String(value)]);
      }
    }
  }
  return normalized;
}

function projectContent(record, kind) {
  const fields = CONTENT_FIELDS[kind];
  if (!fields) throw new Error(`invalid: unsupported event kind ${kind}`);
  return Object.fromEntries(
    fields
      .filter((field) => record[field] !== undefined && record[field] !== null)
      .map((field) => [field, record[field]]),
  );
}

function eventHash(event) {
  const { content_hash: _ignored, ...hashable } = event;
  return createHash("sha256").update(canonicalJson(hashable)).digest("hex");
}

export function toMemoryEvent(record, kind, project, references = {}) {
  if (!record || typeof record !== "object" || Array.isArray(record)) {
    throw new Error("invalid: event record must be an object");
  }
  if (!record.id) throw new Error("invalid: event record id is required");
  if (!project || typeof project !== "string") throw new Error("invalid: event project is required");
  if (!record.created_at) throw new Error("invalid: event created_at is required");

  const event = {
    event_id: `${kind}:${project}:${record.id}`,
    kind,
    project,
    created_at: record.created_at,
    tags: normalizeEventTags(record.tags, references),
    content: projectContent(record, kind),
  };
  return { ...event, content_hash: eventHash(event) };
}

export function validateMemoryEvent(event) {
  if (!event || typeof event !== "object" || Array.isArray(event)) {
    throw new Error("invalid: event must be an object");
  }
  for (const field of ["event_id", "kind", "project", "created_at", "content_hash"]) {
    if (typeof event[field] !== "string" || !event[field]) {
      throw new Error(`invalid: event ${field} is required`);
    }
  }
  if (!Array.isArray(event.tags) || !event.content || typeof event.content !== "object") {
    throw new Error("invalid: event tags and content are required");
  }
  if (eventHash(event) !== event.content_hash) throw new Error("invalid: event hash mismatch");
  return event;
}

export function parseEventJsonl(jsonl, maxEvents = 10000) {
  if (typeof jsonl !== "string") throw new Error("invalid: JSONL input must be a string");
  const lines = jsonl.split(/\r?\n/).filter((line) => line.trim());
  if (lines.length > maxEvents) throw new Error(`invalid: JSONL exceeds ${maxEvents} events`);
  return lines.map((line, index) => {
    try {
      return validateMemoryEvent(JSON.parse(line));
    } catch (error) {
      throw new Error(`invalid: JSONL line ${index + 1}: ${error.message}`);
    }
  });
}

export function serializeEventJsonl(events, maxEvents = 10000) {
  if (!Array.isArray(events)) throw new Error("invalid: events must be an array");
  if (events.length > maxEvents) throw new Error(`invalid: JSONL exceeds ${maxEvents} events`);
  const validated = events.map(validateMemoryEvent);
  return validated.length ? `${validated.map((event) => JSON.stringify(event)).join("\n")}\n` : "";
}

export function mergeEventState(existingEvents, newEvents, maxEvents = 10000) {
  if (!Array.isArray(existingEvents) || !Array.isArray(newEvents)) {
    throw new Error("invalid: event state must contain arrays");
  }
  const byId = new Map();
  for (const event of [...existingEvents, ...newEvents]) {
    const validated = validateMemoryEvent(event);
    byId.set(validated.event_id, validated);
  }
  if (byId.size > maxEvents) {
    throw new Error(`invalid: event state exceeds ${maxEvents} events; rotate or replace the --state file`);
  }
  return [...byId.values()].sort((left, right) => right.created_at.localeCompare(left.created_at)
    || right.event_id.localeCompare(left.event_id));
}
