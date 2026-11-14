import re
from bs4 import BeautifulSoup, NavigableString

def sanitize_clipboard_html(raw_html: str, color_map: dict = None) -> str:
    """
    Extracts body text, keeps bold, italic, underline, and text color,
    and optionally replaces colors using color_map (e.g., {'#00a933': '#008000'}).
    """
    color_map = {k.lower(): v for k, v in (color_map or {}).items()}
    soup = BeautifulSoup(raw_html, "html.parser")
    
    # Focus only on the body if present
    root = soup.body if soup.body else soup

    # Remove non-content tags completely
    for tag in root(["script", "style", "meta", "link", "head"]):
        tag.decompose()

    def process_node(node):
        if isinstance(node, NavigableString):
            # Normalize LibreOffice newlines into standard spaces
            # return re.sub(r'\s+', ' ', str(node))
            return str(node)

        # Recursively process children first
        inner_html = "".join(process_node(child) for child in node.children)
        if not inner_html.strip() and node.name not in ("br",):
            return inner_html

        # Detect formatting from both tags and inline CSS
        style_attr = node.get("style", "").lower()
        
        is_bold = node.name in ("b", "strong") or bool(re.search(r"font-weight\s*:\s*(bold|[6-9]00)", style_attr))
        is_italic = node.name in ("i", "em") or bool(re.search(r"font-style\s*:\s*italic", style_attr))
        is_underline = node.name == "u" or bool(re.search(r"text-decoration[^;]*underline", style_attr))

        # Detect color from <font color="..."> or style="color: ..."
        color = None
        if node.name == "font" and node.get("color"):
            color = node.get("color").strip().lower()
        else:
            color_match = re.search(r"(?<![a-z-])color\s*:\s*([^;\"']+)", style_attr)
            if color_match:
                color = color_match.group(1).strip().lower()

        # Replace color if it's in your mapping dictionary
        if color and color in color_map:
            color = color_map[color]

        # Wrap with clean tags
        result = inner_html
        if color:
            result = f'<span style="color: {color};">{result}</span>'
        if is_underline:
            result = f"<u>{result}</u>"
        if is_italic:
            result = f"<i>{result}</i>"
        if is_bold:
            result = f"<b>{result}</b>"

        # Preserve paragraph breaks
        if node.name in ("p", "div"):
            return f"{result.strip().replace("\n", " ")}"

        return result

    cleaned = "".join(process_node(child) for child in root.children)
    # Clean up empty paragraphs or double spaces
    cleaned = re.sub(r"<div>\s*</div>", "", cleaned)
    return cleaned.strip()