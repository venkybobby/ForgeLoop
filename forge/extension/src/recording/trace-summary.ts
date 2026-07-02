import { collectEventDomains } from '@/shared/events';
import type { CapturedEvent, RecordingRow, RedactionClass, TraceSummary } from '@/shared/types';
import { db } from '@/storage/db';

// Deep-walk an event and tally every redaction by class. Redactions live on
// RedactedValue objects ({ value, redaction: { classes } }) scattered through
// many event shapes, plus FormSummary fields ({ redactionClasses }). Walking
// generically keeps this correct as event schemas evolve.
function tallyRedactions(node: unknown, counts: Record<string, number>, depth = 0): void {
  if (!node || typeof node !== 'object' || depth > 40) return;
  if (Array.isArray(node)) {
    for (const item of node) tallyRedactions(item, counts, depth + 1);
    return;
  }
  const obj = node as Record<string, unknown>;
  const redaction = obj.redaction as { classes?: unknown } | undefined;
  if (redaction && Array.isArray(redaction.classes)) {
    for (const cls of redaction.classes as RedactionClass[]) {
      counts[cls] = (counts[cls] ?? 0) + 1;
    }
  }
  if (Array.isArray(obj.redactionClasses)) {
    for (const cls of obj.redactionClasses as RedactionClass[]) {
      counts[cls] = (counts[cls] ?? 0) + 1;
    }
  }
  for (const key of Object.keys(obj)) {
    if (key === 'redaction' || key === 'redactionClasses') continue;
    tallyRedactions(obj[key], counts, depth + 1);
  }
}

export function shouldUseLiveTraceSummary(recording: RecordingRow): boolean {
  return recording.status === 'recording' || recording.status === 'failed';
}

export async function buildLiveTraceSummary(
  recording: RecordingRow,
  options: { now?: () => number } = {}
): Promise<TraceSummary> {
  const [events, blobs] = await Promise.all([
    db.events.where('trace_id').equals(recording.trace_id).toArray(),
    db.blobs.where('trace_id').equals(recording.trace_id).toArray(),
  ]);

  const domains = new Set<string>();
  const eventCounts: Record<string, number> = {};
  const redactionCounts: Record<string, number> = {};
  let screenshotEvents = 0;
  let videoChunkEvents = 0;

  for (const event of events) {
    eventCounts[event.kind] = (eventCounts[event.kind] ?? 0) + 1;
    collectEventDomains(domains, event);
    tallyRedactions(event, redactionCounts);
    if (event.kind === 'screenshot') screenshotEvents += 1;
    if (event.kind === 'video_chunk') videoChunkEvents += 1;
  }

  const redactionTotal = Object.values(redactionCounts).reduce((sum, n) => sum + n, 0);

  const uploadableBlobs = blobs.filter((blob) => !blob.excluded_from_upload);
  const screenshotBlobs = uploadableBlobs.filter(
    (blob) => blob.kind === 'screenshot'
  ).length;
  const videoBlobs = uploadableBlobs.filter(
    (blob) => blob.kind === 'video'
  ).length;

  return {
    domains: [...domains].sort(),
    duration_ms: durationFor(
      recording,
      events,
      options.now ?? (() => Date.now())
    ),
    event_counts: eventCounts,
    screenshot_count: blobs.length > 0 ? screenshotBlobs : screenshotEvents,
    video_chunk_count: blobs.length > 0 ? videoBlobs : videoChunkEvents,
    redactions: redactionCounts as NonNullable<TraceSummary['redactions']>,
    redaction_total: redactionTotal,
  };
}

function durationFor(
  recording: RecordingRow,
  events: CapturedEvent[],
  now: () => number
): number {
  const started = Date.parse(recording.envelope.started_at);
  if (!Number.isFinite(started)) return 0;

  const ended = recording.envelope.ended_at
    ? Date.parse(recording.envelope.ended_at)
    : NaN;
  if (Number.isFinite(ended)) return Math.max(0, ended - started);

  const latestEventTimestamp = latestEventTime(events);
  if (recording.status === 'recording') {
    return Math.max(
      0,
      Math.max(now(), latestEventTimestamp ?? started) - started
    );
  }

  const fallbackEnd =
    latestEventTimestamp ?? recording.updated_at ?? recording.created_at;
  return Math.max(0, fallbackEnd - started);
}

function latestEventTime(events: CapturedEvent[]): number | undefined {
  const timestamps = events
    .map((event) => event.timestamp)
    .filter(Number.isFinite);
  return timestamps.length > 0 ? Math.max(...timestamps) : undefined;
}
