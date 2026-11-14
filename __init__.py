
from aqt import gui_hooks
from aqt.qt import *
from aqt.utils import showInfo
import html
from .sanitize_clipboard_html import sanitize_clipboard_html
SEPARATOR = "---"

def setup_bulk_import(editor):
    parent = editor.parentWindow

    # avoid duplicate injection
    if hasattr(editor, "bulk_import_initialized"):
        return

    editor.bulk_import_initialized = True

    # main container
    container = QWidget()
    layout = QVBoxLayout()

    # label
    label = QLabel("Bulk Cards")
    layout.addWidget(label)

    # textarea
    textarea = QTextEdit()
    br = "\n\n"
    textarea.setPlaceholderText(
        f"---{br}Card{br}Front:{br}Your front content{br}Back:{br}Your back content{br}---"
    )
    textarea.setMinimumHeight(150)
    layout.addWidget(textarea)

    # button
    buttons_layout = QHBoxLayout()

    paste_button = QPushButton("Paste Text")
    buttons_layout.addWidget(paste_button)

    paste_html_button = QPushButton("Paste HTML")
    buttons_layout.addWidget(paste_html_button)

    load_button = QPushButton("Load Default Align")
    buttons_layout.addWidget(load_button)

    load_button_left = QPushButton("Load Left Align")
    buttons_layout.addWidget(load_button_left)

    layout.addLayout(buttons_layout)

    container.setLayout(layout)

    # add widget into Add Cards window# Toggle button OUTSIDE the container
    toggle_button = QPushButton("Hide Bulk Cards")

    def toggle_bulk():
        visible = container.isVisible()

        container.setVisible(not visible)

        toggle_button.setText(
            "Hide Bulk Cards" if not visible else "Show Bulk Cards"
        )

    toggle_button.clicked.connect(toggle_bulk)


    # Add both to Anki
    editor.outerLayout.addWidget(toggle_button)
    editor.outerLayout.addWidget(container)

    def paste_clipboard():
        text = QApplication.clipboard().text()

        if text:
            textarea.setPlainText(text)

    def paste_clipboard_html():
        text = QApplication.clipboard().text()

        mime_data = QApplication.clipboard().mimeData()

        if mime_data.hasHtml():
            text = mime_data.html()
        else:
            # Fallback to plain text if no HTML is in the clipboard
            text = mime_data.text()

        if text:
            textarea.setPlainText(sanitize_clipboard_html(text))

    def remove_backslash(text: str) -> str:
        if text.endswith('\\'):
            return text[:-1]
        return text

    def format_line(text: str, align: str = "default") -> str:
        formated = text

        if formated:
            if align == "default":
                formated = f"<div>{text}</div>"
            elif align == "left":
                formated = f'<div style="text-align: left;">{text}</div>'

        return formated

    def load_next_card(align: str = "default"):
        content = textarea.toPlainText()

        if not content:
            return

        cards = [c for c in content.split(SEPARATOR) if c]

        if not cards:
            return

        current_card = { 
            "lines": cards[0].splitlines(),
            "front": [],
            "back": []
        }

        has_prev_empty_line = False
        pass_line_with_content = False
        is_front = None
        black_list = ["disabled", "skip", "suspend", "not add"]
        for line in current_card.get("lines"):
            if line.lower().startswith("card"):
                if any(f"{tag}" in line.lower() for tag in black_list):
                    break
            if line.lower().startswith("front:"):
                pass_line_with_content = False
                is_front = True
                continue
            elif line.lower().startswith("back:"):
                pass_line_with_content = False
                is_front = False
                continue
            elif not line.strip(): # empty line
                has_prev_empty_line = True
                continue
            # filters and formatting by line
            new_line = line
            
            # remote backslash at the end of line
            new_line = remove_backslash(new_line)

            # remote spaces at the end of line
            new_line = new_line.rstrip()

            # format the lines adding div to break lines
            new_line = format_line(new_line, align)

            # escape multiple spaces (even quantity)
            new_line = new_line.replace("  ", "&nbsp;&nbsp;")

            if has_prev_empty_line and pass_line_with_content:
                new_line = "<br>" + new_line
                has_prev_empty_line = False

            if line.strip(): # line with content
                pass_line_with_content = True
                has_prev_empty_line = False

            if is_front == True:
                current_card["front"].append(new_line)
            elif is_front == False:
                current_card["back"].append(new_line)

        # set fields
        editor.note.fields[0] = "".join(current_card.get("front"))
        editor.note.fields[1] = "".join(current_card.get("back"))

        editor.loadNote()

        # remove imported card
        remaining = cards[1:]
        textarea.setPlainText(f"{SEPARATOR}".join(remaining))

    paste_button.clicked.connect(paste_clipboard)
    paste_html_button.clicked.connect(paste_clipboard_html)
    load_button.clicked.connect(lambda x : load_next_card())
    load_button_left.clicked.connect(lambda x : load_next_card('left'))


# hook

gui_hooks.editor_did_init.append(setup_bulk_import)

