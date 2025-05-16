#!/usr/bin/env python3
import re
import argparse
import os
import sys

# Regular expressions
TIME_RE = re.compile(r"\d{1,2}:\d{2} [AP]M")
PREVIEW_RE = re.compile(r"^(.+?) by (?P<speaker>.+)$")


def load_lines(path):
    try:
        return open(path, encoding='utf-8').read().splitlines()
    except Exception as e:
        print(f"Error reading '{path}': {e}", file=sys.stderr)
        sys.exit(1)


def save_output(entries, out_path):
    try:
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write("\n\n".join(entries))
    except Exception as e:
        print(f"Error writing '{out_path}': {e}", file=sys.stderr)
        sys.exit(1)


def process_reference(lines, i, entries):
    """
    Parses 'Begin Reference' blocks into formatted entries.
    """
    if not lines[i].strip().startswith("Begin Reference"):
        return None

    n = len(lines)
    j = i + 1
    # Skip blank lines
    while j < n and not lines[j].strip():
        j += 1
    if j >= n:
        return n

    # Referrer
    ref_sender = lines[j].strip()
    j += 1

    # Skip blanks
    while j < n and not lines[j].strip():
        j += 1
    if j >= n:
        return j

    # Reference timestamp
    tm_line = lines[j].strip()
    m = TIME_RE.search(tm_line)
    ref_time = m.group(0) if m else tm_line
    j += 1

    # Skip blanks
    while j < n and not lines[j].strip():
        j += 1
    if j >= n:
        return j

    # Original sender
    orig_sender = lines[j].strip()
    j += 1

    # Skip blanks
    while j < n and not lines[j].strip():
        j += 1
    if j >= n:
        return j

    # Original timestamp or message line
    orig_line = lines[j].strip()
    m2 = TIME_RE.search(orig_line)
    if m2:
        orig_time = m2.group(0)
        j += 1
        # Skip blanks
        while j < n and not lines[j].strip():
            j += 1
        # Original message
        orig_msg = lines[j].strip() if j < n else ""
        j += 1
    else:
        orig_time = ""
        orig_msg = orig_line
        j += 1

    # Follow-up lines
    follow_up = []
    while j < n and lines[j].strip():
        follow_up.append(lines[j].strip())
        j += 1

    # Construct entry
    entry = f"[{ref_time}][{ref_sender}][REFERENCE MESSAGE ({orig_time}) ({orig_sender})({orig_msg})]"
    if follow_up:
        entry += " " + " ".join(follow_up)

    entries.append(entry)
    return j


def skip_preview(lines, i):
    raw = lines[i].strip()
    m = PREVIEW_RE.match(raw)
    if not m:
        return None
    speaker = m.group('speaker').strip()
    j = i + 1
    while j < len(lines) and not lines[j].strip():
        j += 1
    if j < len(lines) and lines[j].strip() == speaker and j+1 < len(lines) and TIME_RE.search(lines[j+1]):
        return j
    return None


def process_standard(lines, i, entries):
    # Standard message: name on this line, time on next, then the body
    if i+1 >= len(lines) or not TIME_RE.search(lines[i+1]):
        return None
    name = lines[i].strip()
    tm = TIME_RE.search(lines[i+1]).group(0)
    j = i + 2
    if j < len(lines) and not lines[j].strip():
        j += 1

    body = []
    while j < len(lines) and not lines[j].startswith("Begin Reference") and not (j+1 < len(lines) and TIME_RE.search(lines[j+1])):
        txt = lines[j].strip()
        if txt.lower() == 'image':
            body.append('IMAGE ADDED TO CHAT')
        elif not PREVIEW_RE.match(txt):
            body.append(txt)
        j += 1

    entries.append(f"[{tm}][{name}] {' '.join(body).strip()}")
    return j


def main():
    parser = argparse.ArgumentParser(description='Clean transcript with reference parsing')
    parser.add_argument('input_file', help='Raw transcript .txt')
    parser.add_argument('-o', '--output', default='Formatted_Transcript.txt', help='Output filename')
    args = parser.parse_args()

    lines = load_lines(args.input_file)
    entries = []
    i = 0
    n = len(lines)
    while i < n:
        ni = process_reference(lines, i, entries)
        if ni is not None:
            i = ni
            continue
        ni = skip_preview(lines, i)
        if ni is not None:
            i = ni
            continue
        ni = process_standard(lines, i, entries)
        if ni is not None:
            i = ni
            continue
        i += 1

    save_output(entries, os.path.basename(args.output))
    print(f"Success: cleaned transcript → {args.output}")

if __name__ == '__main__':
    main()
