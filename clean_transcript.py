#!/usr/bin/env python3
import re
import argparse
import os
import sys

# Patterns
TIME_RE = re.compile(r"\d{1,2}:\d{2} [AP]M")
BEGIN_REF_RE = re.compile(r"^Begin Reference,\s*(?P<preview>.+?)\.\.\. by (?P<orig>.+)$")
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
    mref = BEGIN_REF_RE.match(lines[i].strip())
    if not mref:
        return None
    orig = mref.group('orig').strip()
    referrer = lines[i+1].strip()
    rt = TIME_RE.search(lines[i+2])
    ref_time = rt.group(0) if rt else ''
    # Skip blanks to original speaker
    j = i + 3
    while j < len(lines) and not lines[j].strip(): j += 1

    speaker = lines[j].strip()
    st = TIME_RE.search(lines[j+1])
    speaker_time = st.group(0) if st else ''
    # Collect original message lines
    k = j + 2
    orig_msg = []
    while k < len(lines) and lines[k].strip():
        orig_msg.append(lines[k].strip())
        k += 1
    # Skip blanks to comment
    while k < len(lines) and not lines[k].strip(): k += 1
    comment = []
    while k < len(lines) and not BEGIN_REF_RE.match(lines[k].strip()) and not (k+1 < len(lines) and TIME_RE.search(lines[k+1])):
        comment.append(lines[k].strip())
        k += 1
    entry = f"[{ref_time}][{referrer}][REFERENCE MESSAGE: ({speaker})({speaker_time})({' '.join(orig_msg)})]"
    if comment:
        entry += ' ' + ' '.join(comment)
    entries.append(entry)
    return k


def skip_preview(lines, i):
    raw = lines[i].strip()
    m = PREVIEW_RE.match(raw)
    if not m:
        return None
    speaker = m.group('speaker').strip()
    j = i + 1
    while j < len(lines) and not lines[j].strip(): j += 1
    if j < len(lines) and lines[j].strip() == speaker and j+1 < len(lines) and TIME_RE.search(lines[j+1]):
        return j
    return None


def process_standard(lines, i, entries):
    if i+1 >= len(lines) or not TIME_RE.search(lines[i+1]):
        return None
    name = lines[i].strip()
    tm = TIME_RE.search(lines[i+1]).group(0)
    j = i + 2
    if j < len(lines) and not lines[j].strip(): j += 1
    body = []
    while j < len(lines) and not BEGIN_REF_RE.match(lines[j].strip()) and not (j+1 < len(lines) and TIME_RE.search(lines[j+1])):
        txt = lines[j].strip()
        if txt.lower() == 'image':
            body.append('IMAGE ADDED TO CHAT')
        elif not PREVIEW_RE.match(txt):
            body.append(txt)
        j += 1
    entries.append(f"[{tm}][{name}] {' '.join(body).strip()}")
    return j


def main():
    parser = argparse.ArgumentParser(description='Clean transcript, modularized into 3 functions')
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
