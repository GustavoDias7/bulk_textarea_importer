
from aqt import gui_hooks
from aqt.qt import *
from aqt.utils import showInfo
import html

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

    load_button = QPushButton("Load Next Card (Align default)")
    buttons_layout.addWidget(load_button)

    load_button_left = QPushButton("Load Next Card (Align left)")
    buttons_layout.addWidget(load_button_left)

    paste_button = QPushButton("Paste Clipboard")
    buttons_layout.addWidget(paste_button)

    buttons_layout_not_escaped = QPushButton("Load Next Card (Not escaped)")
    buttons_layout.addWidget(buttons_layout_not_escaped)

    layout.addLayout(buttons_layout)

    container.setLayout(layout)

    # add widget into Add Cards window
    editor.outerLayout.addWidget(container)

    def paste_clipboard():
        text = QApplication.clipboard().text()

        if text:
            textarea.setPlainText(text)

    # def format(value: str):
    #     formated = f'<div style="text-align: left;">{html.escape(value)}</div>'
    #     formated = formated.replace("  ", "&nbsp;&nbsp;")
    #     return formated

    def load_next_card(align: str = "default"):
        content = textarea.toPlainText()

        if not content:
            return

        cards = [c for c in content.split(SEPARATOR) if c]

        if not cards:
            return

        first_card = cards[0]
        front_card = []
        back_card = []

        is_front = None
        black_list = ["disabled", "skip"]

        lines = first_card.splitlines()
        for index, line in enumerate(lines):
            if line.lower().startswith("card"):
                if any(f"[{tag}]" in line.lower() for tag in black_list):
                    break
            if line.lower().startswith("front:"):
                is_front = True
                continue
            elif line.lower().startswith("back:"):
                is_front = False
                continue

            formated = ""
            if not line.strip():
                if index > 0 and lines[index - 1].lower().startswith("front:"):
                    # This line is empty and it is before the front mark
                    pass
                elif index > 0 and lines[index - 1].lower().startswith("back:"):
                    # This line is empty and it is before the back mark
                    pass
                elif index < len(lines) - 1 and not lines[index + 1].strip():
                    # This line is empty and next line is empty too.
                    pass
                elif index > 0 and not lines[index - 1].strip():
                    # This line is empty and previous line is empty too.
                    pass
                elif index == len(lines) - 1:
                    pass
                else:
                    formated = f"<br>"
            else:
                if align == "default":
                    formated = f"<div>{html.escape(line.rstrip())}</div>"
                elif align == "left":
                    formated = f'<div style="text-align: left;">{html.escape(line.rstrip())}</div>'
                elif align == "not_escaped":
                    formated = line.rstrip()
                formated = formated.replace("  ", "&nbsp;&nbsp;")

            if is_front == True:
                front_card.append(formated)
            elif is_front == False:
                back_card.append(formated)

        # set fields
        editor.note.fields[0] = "".join(front_card)
        editor.note.fields[1] = "".join(back_card)

        editor.loadNote()

        # remove imported card
        remaining = cards[1:]
        textarea.setPlainText(f"{SEPARATOR}".join(remaining))

    paste_button.clicked.connect(paste_clipboard)
    buttons_layout_not_escaped.clicked.connect(lambda x : load_next_card('not_escaped'))
    load_button.clicked.connect(lambda x : load_next_card())
    load_button_left.clicked.connect(lambda x : load_next_card('left'))


# hook

gui_hooks.editor_did_init.append(setup_bulk_import)

