
#!/usr/bin/env python3
import re
import argparse
import os
import sys

# Regex patterns
time_pattern = r"\d{1,2}:\d{2} [AP]M"
header_re = re.compile(
    r"(?m)^(?P<name>.+?)\n"
    r"(?:(?:Yesterday|\d{1,2}/\d{1,2}/\d{4})\s+)?"
    r"(?P<time>" + time_pattern + r")\n\n"
)
preview_re = re.compile(r"\.\.\.\s*by\s*(?P<orig>.+)$")

# Load and save
def load_text(path):
    try:
        return open(path, encoding='utf-8').read()
    except Exception as e:
        print(f"Error reading '{path}': {e}", file=sys.stderr)
        sys.exit(1)

def save_output(lines, out_path):
    try:
        open(out_path, 'w', encoding='utf-8').write("\n\n".join(lines))
    except Exception as e:
        print(f"Error writing '{out_path}': {e}", file=sys.stderr)
        sys.exit(1)

# Preprocess: remove Begin Reference lines and full-line truncated previews

def preprocess(text):
    lines = text.splitlines(keepends=True)
    out = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if line.startswith('Begin Reference'):
            # skip this tag
            i += 1
            continue
        m = preview_re.search(line.strip())
        if m and i+1 < n:
            # check next non-empty is orig speaker and next line is time
            speaker = m.group('orig').strip()
            # find next non-empty
            j = i+1
            while j<n and not lines[j].strip(): j+=1
            if j<n and lines[j].strip() == speaker and j+1<n and re.search(time_pattern, lines[j+1]):
                i += 1
                continue
        out.append(line)
        i += 1
    return ''.join(out)

# Extract raw blocks

def extract_blocks(text):
    matches = list(header_re.finditer(text))
    blocks = []
    for idx, m in enumerate(matches):
        name = m.group('name').strip()
        time = m.group('time').strip()
        start = m.end()
        end = matches[idx+1].start() if idx+1 < len(matches) else len(text)
        body = text[start:end].strip()
        # collapse lines
        lines = [l.strip() for l in body.splitlines() if l.strip()]
        # handle image
        saw_image = False
        parts = []
        for l in lines:
            if l.lower() == 'image': saw_image=True
            else: parts.append(l)
        msg = ' '.join(parts)
        if saw_image:
            msg = (msg + ' IMAGE ADDED TO CHAT') if msg else 'IMAGE ADDED TO CHAT'
        blocks.append({'time': time, 'name': name, 'msg': msg})
    return blocks

# Consolidate inline references

def consolidate_refs(blocks):
    out = []
    for i, b in enumerate(blocks):
        m = preview_re.search(b['msg'])
        if m:
            orig = m.group('orig').strip()
            # find next block for orig
            ref_msg = ''
            for b2 in blocks[i+1:]:
                if b2['name'] == orig:
                    ref_msg = b2['msg']
                    break
            # new comment = msg without truncated preview
            new_comment = preview_re.sub('', b['msg']).strip()
            entry = f"[{b['time']}][{b['name']}][REFERENCE MESSAGE: {ref_msg}]"
            if new_comment:
                entry += ' ' + new_comment
            out.append(entry)
        else:
            out.append(f"[{b['time']}][{b['name']}] {b['msg']}")
    return out

# Main
def main():
    p = argparse.ArgumentParser(description='Clean transcript to [time][name] format')
    p.add_argument('input_file')
    p.add_argument('-o','--output', default='Formatted_Transcript.txt')
    args = p.parse_args()

    raw = load_text(args.input_file)
    pre = preprocess(raw)
    blocks = extract_blocks(pre)
    lines = consolidate_refs(blocks)
    if not lines:
        print('Warning: no entries parsed', file=sys.stderr)
    out_path = os.path.join(os.getcwd(), os.path.basename(args.output))
    save_output(lines, out_path)
    print(f"Success: cleaned transcript → {out_path}")

if __name__ == '__main__':
    main()

