#!/usr/bin/env python3
"""Convert resumx-format markdown resumes to styled HTML."""
import re
import os

CSS_PATH = os.path.expanduser("~/projects/github/Resume/resume-template.css")
OUT_DIR = os.path.expanduser("~/projects/github/Resume")


def parse_frontmatter(text):
    lines = text.split('\n')
    if not lines or lines[0].strip() != '---':
        return {}, text
    end = 1
    while end < len(lines) and lines[end].strip() != '---':
        end += 1
    content = '\n'.join(lines[end+1:])
    return {}, content.strip()


def md_to_html(md_text):
    _, body = parse_frontmatter(md_text)
    lines = body.split('\n')
    html = []
    i = 0
    n = len(lines)

    # State
    in_entry = False       # inside a ### block
    entry_bullets = []     # bullets collected for current ### entry
    section_bullets = []   # bullets collected for current ## section (outside ###)
    in_section_bullets = False  # we have opened a <ul> for section bullets
    in_dl = False          # inside a <dl> for definition list

    def close_entry():
        nonlocal in_entry, entry_bullets, in_section_bullets, section_bullets
        if in_entry or entry_bullets:
            html.append('<ul>')
            for b in entry_bullets:
                html.append(f'<li>{b}</li>')
            html.append('</ul>')
            entry_bullets = []
        if in_entry:
            html.append('</div>')
            in_entry = False

    def close_section_bullets():
        nonlocal in_section_bullets, section_bullets
        if section_bullets:
            html.append('<ul>')
            for b in section_bullets:
                html.append(f'<li>{b}</li>')
            html.append('</ul>')
            section_bullets = []

    def close_dl():
        nonlocal in_dl
        if in_dl:
            html.append('</dl>')
            in_dl = False

    def flush_bullets():
        close_entry()
        close_section_bullets()
        close_dl()

    while i < n:
        line = lines[i]
        stripped = line.strip()

        # --- frontmatter separator (skip)
        if stripped == '---' and i < 3:
            i += 1
            continue

        # # Title
        m = re.match(r'^# (.+)', line)
        if m:
            name = m.group(1).strip()
            html.append(f'<div class="header"><div class="name">{name}</div>')
            i += 1
            contact = []
            while i < n and not lines[i].startswith('#'):
                if lines[i].strip():
                    contact.append(lines[i].strip())
                i += 1
            sep = ' <span class="sep">|</span> '
            # Split long contact into multiple lines (each markdown line = one contact line)
            if len(contact) <= 1:
                html.append(f'<div class="contact">{sep.join(contact)}</div></div>')
            else:
                html.append('<div class="contact">')
                for cl in contact:
                    html.append(f'<div class="contact-line">{cl}</div>')
                html.append('</div></div>')
            continue

        # ## Section
        m = re.match(r'^## (.+)', line)
        if m:
            flush_bullets()
            section_name = m.group(1).strip()
            section_id = section_name.lower().replace(' ', '-')
            html.append(f'<div class="section" id="{section_id}">')
            html.append(f'<div class="section-title">{section_name}</div>')
            i += 1
            continue

        # ### Entry
        m = re.match(r'^### (.+)', line)
        if m:
            close_entry()
            close_section_bullets()
            entry_text = m.group(1).strip()
            title = entry_text
            date = ''
            if '||' in entry_text:
                parts = [p.strip() for p in entry_text.split('||')]
                title = parts[0]
                date = ' || '.join(parts[1:])
            html.append('<div class="entry">')
            if date:
                html.append(f'<div class="entry-header"><div class="entry-title">{title}</div><div class="entry-date">{date}</div></div>')
            else:
                html.append(f'<div class="entry-title">{title}</div>')
            in_entry = True

            # Look for _subtitle_ || location on next line(s)
            i += 1
            while i < n and not lines[i].strip():
                i += 1
            if i < n:
                m2 = re.match(r'^_(.+?)_(?:\s*\|\|\s*(.+))?$', lines[i].strip())
                if m2:
                    subtitle = m2.group(1)
                    location = m2.group(2) if m2.group(2) else ''
                    if location:
                        html.append(f'<div class="entry-meta"><div class="entry-subtitle">{subtitle}</div><div class="entry-location">{location}</div></div>')
                    else:
                        html.append(f'<div class="entry-subtitle">{subtitle}</div>')
                    i += 1
            continue

        # - bullets
        if stripped.startswith('- '):
            bullet_text = stripped[2:]
            bullet_text = re.sub(r'`([^`]+)`', r'<code>\1</code>', bullet_text)
            if in_entry:
                entry_bullets.append(bullet_text)
            else:
                section_bullets.append(bullet_text)
                in_section_bullets = True
            i += 1
            continue

        # Empty lines inside entry → keep entry open
        if in_entry and not stripped:
            i += 1
            continue
        elif in_section_bullets and not stripped.startswith('- '):
            pass  # keep section bullets open until next ## or ###

        # Numbered lines (1. 2. 3.) - treat as plain text
        if re.match(r'^\d+[\.\、]', stripped) and in_entry:
            entry_bullets.append(stripped)
            i += 1
            continue

        # "**核心业绩：**" etc - treat as a subtitle inside entry
        if stripped.startswith('**') and stripped.endswith('**') and in_entry:
            entry_bullets.append(stripped.strip('*'))
            i += 1
            continue

        # Definition list: term followed by line starting with ':'
        if i + 1 < n and lines[i+1].strip().startswith(':'):
            if not in_dl:
                close_section_bullets()
                close_entry()
                html.append('<dl class="skills-dl">')
                in_dl = True
            term = stripped.replace('**', '')
            html.append(f'<dt>{term}</dt>')
            i += 1
            desc = lines[i].strip().lstrip(':').strip().replace('**', '')
            html.append(f'<dd>{desc}</dd>')
            i += 1
            continue
        # Close dl only when we encounter a heading or bullet (not empty lines)
        if in_dl and (stripped.startswith('#') or stripped.startswith('- ') or re.match(r'^\d+[\.\、]', stripped)):
            html.append('</dl>')
            in_dl = False

        i += 1

    # Close remaining
    close_entry()
    close_section_bullets()
    html.append('</div>')  # close last section

    return '\n'.join(html)


def build_html(md_file):
    with open(md_file, 'r', encoding='utf-8') as f:
        md_text = f.read()

    body_html = md_to_html(md_text)
    title = os.path.splitext(os.path.basename(md_file))[0]

    css_content = open(CSS_PATH, 'r', encoding='utf-8').read()

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
{css_content}
</style>
</head>
<body>
<div class="page">
{body_html}
</div>
</body>
</html>'''


def main():
    md_files = [
        '俞凡简历_通用版.md',
        '俞凡简历_技术专家.md',
        '俞凡简历_架构版.md',
        '俞凡简历_云原生架构师.md',
        'YuFan_Resume_EN.md',
    ]
    for mdf in md_files:
        mdf_path = os.path.join(OUT_DIR, mdf)
        if not os.path.exists(mdf_path):
            print(f"SKIP: {mdf}")
            continue
        html = build_html(mdf_path)
        out_name = os.path.splitext(mdf)[0] + '.html'
        out_path = os.path.join(OUT_DIR, out_name)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"OK: {out_name}")


if __name__ == '__main__':
    main()
