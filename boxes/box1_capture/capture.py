"""
Box 1 — Signal Capture
Frozen. No redesign.
"""

from datetime import datetime, timezone


def capture(raw_input, source_tag: str = "unknown") -> dict:
    """
    Box 1 Entrypoint
    
    Wraps any input into CanonicalSignal.
    No rejection. No interpretation. No validation.
    """
    
    # Block 1.1 — Capture (no loss, no filtering)
    signal_blob = raw_input
    
    # Block 1.2 — Normalize (structural only, idempotent)
    if isinstance(signal_blob, str):
        canonical_form = signal_blob  # preserve exactly
        encoding = "utf-8"
    elif isinstance(signal_blob, bytes):
        canonical_form = signal_blob
        encoding = "binary"
    else:
        canonical_form = signal_blob
        encoding = "unknown"
    
    # Block 1.3 — Source Tagging
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Block 1.4 — Emit (CanonicalSignal)
    canonical_signal = {
        "raw_payload": canonical_form,
        "timestamp": timestamp,
        "source_tag": source_tag,
        "encoding": encoding,
        "flags": {
            "malformed": False,
            "complete": True
        }
    }
    
    # Stdout trace for execution proof
    print(f"[BOX1] Captured signal at {timestamp}")
    print(f"[BOX1] Payload: {repr(canonical_form)}")
    print(f"[BOX1] Source: {source_tag}")
    
    return canonical_signal
