import sys
import webbrowser
from pathlib import Path
import markdown2

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<style>
    body {{
        max-width: 900px;
        margin: 40px auto;
        padding: 0 20px;
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        line-height: 1.7;
        font-size: 16px;
        background: #fafafa;
        color: #222;
    }}
    h1, h2, h3, h4 {{
        margin-top: 1.4em;
        margin-bottom: 0.5em;
        font-weight: 600;
    }}
    pre {{
        padding: 12px;
        border-radius: 6px;
        background: #111;
        color: #f5f5f5;
        overflow-x: auto;
        font-size: 14px;
    }}
    code {{
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
    }}
    a {{
        text-decoration: none;
    }}
    a:hover {{
        text-decoration: underline;
    }}
    table {{
        border-collapse: collapse;
        margin: 16px 0;
        width: 100%;
    }}
    th, td {{
        border: 1px solid #ddd;
        padding: 8px 10px;
        text-align: left;
    }}
    img {{
        max-width: 100%;
        height: auto;
    }}
    ul, ol {{
        padding-left: 24px;
    }}
</style>
</head>
<body>
{body}
</body>
</html>
"""

def choose_md_file_from_dir():
    """Selects a .md file from the current directory if no filename is provided."""
    md_files = sorted(Path.cwd().glob("*.md"))

    if not md_files:
        print("No .md files found in the current directory.")
        sys.exit(1)

    if len(md_files) == 1:
        print(f"Found one file: {md_files[0].name}")
        return md_files[0]

    print("Multiple Markdown files found. Choose a file by number:")
    for idx, f in enumerate(md_files, start=1):
        print(f"{idx}. {f.name}")

    try:
        choice = int(input("File number: ").strip())
        if 1 <= choice <= len(md_files):
            return md_files[choice - 1]
    except ValueError:
        pass

    print("Invalid choice. Exiting.")
    sys.exit(1)

def get_md_path():
    """Determines the Markdown file path from CLI arguments or prompts user selection."""
    if len(sys.argv) >= 2:
        candidate = Path(sys.argv[1])

        if not candidate.is_absolute():
            candidate = Path.cwd() / candidate

        if candidate.exists() and candidate.suffix.lower() == ".md":
            return candidate.resolve()

        print("Specified file does not exist or is not a .md file. Searching in current directory.")

    return choose_md_file_from_dir()

def main():
    """Main function to convert a Markdown file to styled HTML and open in browser."""
    md_path = get_md_path()

    html_body = markdown2.markdown_path(
        md_path,
        extras=[
            "fenced-code-blocks",
            "tables",
            "strike",
            "toc",
            "metadata"
        ]
    )

    html_content = TEMPLATE.format(
        title=md_path.name,
        body=html_body
    )

    html_path = md_path.with_suffix("")
    html_path = html_path.parent / f"{html_path.stem}._preview.html"
    html_path.write_text(html_content, encoding="utf-8")

    webbrowser.open(html_path.as_uri())
    print(f"Preview created: {html_path}")

if __name__ == "__main__":
    main()
