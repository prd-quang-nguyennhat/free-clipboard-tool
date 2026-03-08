import os
import sys
import uuid
import hashlib
import shutil

from PyQt6.QtCore import Qt, QTimer, QPoint, QSize
from PyQt6.QtGui import QColor, QAction, QImage, QPixmap, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QStyle,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
    QMenu,
)

class ClipboardManager(QWidget):
    WINDOW_TITLE = "Clipboard history"
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    IMAGE_DIR = os.path.join(BASE_DIR, ".images")

    MAX_HISTORY_SAVE = 50
    MIN_WIDTH, MIN_HEIGHT = 370, 600
    CLIPBOARD_CHECK_INTERVAL = 500
    RESTORE_TIMER_DELAY = 800
    MAX_DISPLAY_LENGTH = 40
    TRUNCATION_SUFFIX, TRUNCATION_OFFSET = "...", 37
    ICON_SIZE = QSize(40, 40)

    def __init__(self) -> None:
        """Initialize the manager for a fresh session."""
        super().__init__()

        # --- STARTUP CLEANUP ---
        # Wipe old images every time the app starts for a fresh slate
        if os.path.exists(self.IMAGE_DIR):
            shutil.rmtree(self.IMAGE_DIR)
        os.makedirs(self.IMAGE_DIR)

        self._setup_window()
        self._setup_icons()
        self._setup_system_tray()
        self._setup_ui_components()
        self._apply_styling()
        self._setup_clipboard_monitoring()

        # ONLY load what is currently on the clipboard right now
        self._load_initial_clipboard()

        self._connect_signals()

    def _cleanup_orphaned_images(self) -> None:
        """Delete image files that are no longer in the top 20 list items."""
        referenced_images = set()
        for index in range(self.list_widget.count()):
            item = self.list_widget.item(index)
            if item.data(Qt.ItemDataRole.UserRole + 2) == "image":
                referenced_images.add(os.path.basename(item.data(Qt.ItemDataRole.UserRole)))

        try:
            for filename in os.listdir(self.IMAGE_DIR):
                if filename not in referenced_images:
                    os.remove(os.path.join(self.IMAGE_DIR, filename))
        except Exception as e:
            print(f"Cleanup error: {e}")

    def _add_clipboard_item(self, text: str, is_pinned: bool = False) -> None:
        """Updated to support pre-pinned status from save file."""
        display_text = self._format_display_text(text)
        if is_pinned:
            display_text = f"📌 {display_text}"
        item = QListWidgetItem(display_text)
        item.setData(Qt.ItemDataRole.UserRole, text)
        item.setData(Qt.ItemDataRole.UserRole + 1, is_pinned)
        item.setData(Qt.ItemDataRole.UserRole + 2, "text")
        self._insert_and_style_item(item, is_pinned)
        self._cleanup_orphaned_images() # Keep folder lean

    def _add_image_item(self, content: any, is_pinned: bool = False, is_path: bool = False) -> None:
        image_path = content if is_path else self._save_image_to_file(content)
        if not image_path: return
        display_text = "Image Snippet"
        if is_pinned:
            display_text = f"📌 {display_text}"
        item = QListWidgetItem(display_text)
        item.setData(Qt.ItemDataRole.UserRole, image_path)
        item.setData(Qt.ItemDataRole.UserRole + 1, is_pinned)
        item.setData(Qt.ItemDataRole.UserRole + 2, "image")
        pixmap = QPixmap(image_path).scaled(self.ICON_SIZE, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        item.setIcon(QIcon(pixmap))
        self._insert_and_style_item(item, is_pinned)
        self._cleanup_orphaned_images()

    def _save_image_to_file(self, image: QImage) -> str:
        filename = f"img_{uuid.uuid4().hex[:8]}.png"
        path = os.path.join(self.IMAGE_DIR, filename)
        if image.save(path, "PNG"): return path
        return ""

    def _insert_and_style_item(self, item: QListWidgetItem, is_pinned: bool) -> None:
        if is_pinned:
            item.setForeground(QColor("#ffcc00"))
            self.list_widget.insertItem(0, item)
        else:
            insert_pos = self._get_first_non_pinned_index()
            self.list_widget.insertItem(insert_pos, item)

        # Enforce the 20 item limit in the UI immediately
        while self.list_widget.count() > self.MAX_HISTORY_SAVE:
            self.list_widget.takeItem(self.list_widget.count() - 1)


    def _setup_window(self) -> None:
        """Configure the main window properties including title and minimum size."""
        self.setWindowTitle(self.WINDOW_TITLE)
        self.setMinimumSize(self.MIN_WIDTH, self.MIN_HEIGHT)

    def _setup_icons(self) -> None:
        """Initialize and configure the application icons for window and system tray."""
        self.default_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogContentsView)
        self.setWindowIcon(self.default_icon)

    def _setup_system_tray(self) -> None:
        """Create and configure the system tray icon with click handling."""
        self.tray_icon = QSystemTrayIcon(self.default_icon, self)
        self.tray_icon.show()
        self.tray_icon.activated.connect(self.on_tray_click)

    def _apply_styling(self) -> None:
        style = """
            QWidget { background-color: #1e1e1e; }
            QLabel { color: #8e8e93; font-size: 11px; font-weight: bold; margin-left: 10px; margin-top: 5px; }
            QLineEdit { background-color: #3c3c3c; color: #ffffff; border: 1px solid #555555; border-radius: 5px; padding: 8px; margin: 5px 10px; }
            QLineEdit#current_display { background-color: #2d2d2d; color: #00ccff; border: 1px dashed #007aff; }
            QListWidget { border: none; background-color: #252526; border-radius: 8px; margin: 5px; outline: none; }
            QListWidget::item { padding: 12px; border-bottom: 1px solid #333333; color: #d4d4d4; }
            QListWidget::item:alternate { background-color: #2d2d2d; }
            QListWidget::item:selected { background-color: #094771; color: white; border-radius: 4px; }
            QMenu { background-color: #252526; color: #d4d4d4; border: 1px solid #333333; }
            QMenu::item:selected { background-color: #094771; }
        """
        self.setStyleSheet(style)

    def _setup_ui_components(self) -> None:
        """Create and arrange the main UI components including search bar, label, and list widget."""
        self.layout = QVBoxLayout()
        self.current_label = QLabel("READY TO PASTE")
        self.current_display = QLineEdit()
        self.current_display.setObjectName("current_display")
        self.current_display.setReadOnly(True)
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search history...")

        self.label = QLabel("HISTORY (Double-click to Pin, Right-click to Delete)")

        self.list_widget = QListWidget()
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.setIconSize(self.ICON_SIZE)
        self.layout.addWidget(self.current_label)
        self.layout.addWidget(self.current_display)
        self.layout.addWidget(self.search_bar)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.list_widget)
        self.setLayout(self.layout)

    def _setup_clipboard_monitoring(self) -> None:
        """Initialize clipboard monitoring with a timer to check for changes."""
        self.clipboard = QApplication.clipboard()
        self.last_seen_text = ""
        self.last_seen_image_hash = ""
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_clipboard)
        self.timer.start(self.CLIPBOARD_CHECK_INTERVAL)

    def _load_initial_clipboard(self) -> None:
        mime = self.clipboard.mimeData()
        if mime.hasImage():
            img = self.clipboard.image()
            self.last_seen_image_hash = self._get_image_hash(img)
            self._update_current_display("[Image in Clipboard]")
            self._add_image_item(img)
        else:
            txt = self._get_current_clipboard_text()
            self.last_seen_text = txt
            self._update_current_display(txt)
            if txt.strip(): self._add_clipboard_item(txt)

    def _connect_signals(self) -> None:
        """Connect UI signals to their respective handler methods."""
        self.list_widget.itemClicked.connect(self._copy_item_back)
        self.list_widget.itemDoubleClicked.connect(self.toggle_pin)
        self.search_bar.textChanged.connect(self._filter_list)
        self.list_widget.customContextMenuRequested.connect(self._show_context_menu)

    def _get_image_hash(self, image: QImage) -> str:
        if image.isNull(): return ""
        bits = image.constBits(); bits.setsize(image.sizeInBytes())
        return hashlib.md5(bits).hexdigest()

    def _update_current_display(self, text: str) -> None:
        self.current_display.setText(text.replace('\n', ' '))
        self.current_display.setCursorPosition(0)

    def _show_context_menu(self, position: QPoint) -> None:
        item = self.list_widget.itemAt(position)
        if not item: return
        menu = QMenu()
        del_act = QAction("Delete", self)
        del_act.triggered.connect(lambda: self._delete_item(item))
        menu.addAction(del_act); menu.exec(self.list_widget.mapToGlobal(position))

    def _delete_item(self, item: QListWidgetItem) -> None:
        self.list_widget.takeItem(self.list_widget.row(item))
        self._cleanup_orphaned_images()

    def toggle_pin(self, item) -> None:
        is_pinned = not item.data(Qt.ItemDataRole.UserRole + 1)
        content = item.data(Qt.ItemDataRole.UserRole)
        c_type = item.data(Qt.ItemDataRole.UserRole + 2)
        self.list_widget.takeItem(self.list_widget.row(item))
        if c_type == "image": self._add_image_item(content, is_pinned=is_pinned, is_path=True)
        else: self._add_clipboard_item(content, is_pinned=is_pinned)

    def _get_first_non_pinned_index(self) -> int:
        for i in range(self.list_widget.count()):
            if not self.list_widget.item(i).data(Qt.ItemDataRole.UserRole + 1): return i
        return self.list_widget.count()

    def _filter_list(self, query: str) -> None:
        """Filter the clipboard history list based on the search query.

        Args:
            query: The search string to filter items by.
        """
        query = query.lower()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            full_text = item.text().lower()
            if item.data(Qt.ItemDataRole.UserRole + 2) == "text":
                full_text = item.data(Qt.ItemDataRole.UserRole).lower()
            item.setHidden(query not in full_text)

    def _get_current_clipboard_text(self) -> str:
        """Get the current text content from the system clipboard.

        Returns:
            str: The clipboard text content or empty string if unavailable.
        """
        try:
            return self.clipboard.text() or ""
        except Exception:
            return ""

    def on_tray_click(self, reason) -> None:
        """Handle system tray icon click events.

        Args:
            reason: The type of activation that triggered this event.
        """
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_and_raise()

    def show_and_raise(self) -> None:
        """Show the window and bring it to the front with focus."""
        self.show()
        self.raise_()
        self.activateWindow()

    def check_clipboard(self) -> None:
        mime = self.clipboard.mimeData()
        if mime.hasImage():
            img = self.clipboard.image()
            if not img.isNull():
                h = self._get_image_hash(img)
                if h != self.last_seen_image_hash:
                    self.last_seen_image_hash = h; self.last_seen_text = ""
                    self._update_current_display("[Image Captured]")
                    self._add_image_item(img)
            return
        txt = self._get_current_clipboard_text()
        if txt and txt.strip():
            self._update_current_display(txt)
            if txt != self.last_seen_text:
                self.last_seen_text = txt; self.last_seen_image_hash = ""
                self._add_clipboard_item(txt)
                self._filter_list(self.search_bar.text())

    def _format_display_text(self, text) -> str:
        """Format text for display in the list widget by removing newlines and truncating if necessary.

        Args:
            text: The raw text to format for display.

        Returns:
            str: The formatted text suitable for display in the list widget.
        """
        display_text = text.replace('\n', ' ').strip()
        if len(display_text) > self.MAX_DISPLAY_LENGTH:
            display_text = display_text[:self.TRUNCATION_OFFSET] + self.TRUNCATION_SUFFIX
        return display_text

    def _copy_item_back(self, item) -> None:
        """Copy the selected item's content back to the clipboard.

        Args:
            item: The QListWidgetItem containing the text to copy to clipboard.
        """
        try:
            self.timer.stop()
            content = item.data(Qt.ItemDataRole.UserRole)
            if item.data(Qt.ItemDataRole.UserRole + 2) == "image":
                img = QImage(content); self.clipboard.setImage(img)
                self.last_seen_image_hash = self._get_image_hash(img)
                self._update_current_display("[Image Restored]")
            else:
                self.clipboard.setText(content); self.last_seen_text = content
                self._update_current_display(content)
            QTimer.singleShot(self.RESTORE_TIMER_DELAY, self.timer.start)
        except Exception:
            QTimer.singleShot(self.RESTORE_TIMER_DELAY, self.timer.start)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    manager = ClipboardManager()
    manager.show()
    sys.exit(app.exec())
