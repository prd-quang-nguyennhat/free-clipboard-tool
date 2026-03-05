import json  # Using JSON for cleaner structure than raw .txt
import os
import sys

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
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
)


class ClipboardManager(QWidget):
    WINDOW_TITLE = "Clipboard history"
    STORAGE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".clipboard_history.json")
    MAX_HISTORY_SAVE = 20
    MIN_WIDTH, MIN_HEIGHT = 370, 550
    CLIPBOARD_CHECK_INTERVAL = 500
    RESTORE_TIMER_DELAY = 800
    MAX_DISPLAY_LENGTH = 40
    TRUNCATION_SUFFIX, TRUNCATION_OFFSET = "...", 37

    def __init__(self) -> None:
        """Initialize the clipboard manager with all necessary components.

        Sets up the window, icons, system tray, UI components, styling, and clipboard monitoring.
        Loads saved history from disk and captures the initial clipboard content.
        """
        super().__init__()
        self._setup_window()
        self._setup_icons()
        self._setup_system_tray()
        self._setup_ui_components()
        self._apply_styling()
        self._setup_clipboard_monitoring()

        # Load saved items first, then capture current clipboard
        self._load_history_from_disk()
        self._load_initial_clipboard()

        self._connect_signals()

    # --- NEW: PERSISTENCE LOGIC ---

    def _save_history_to_disk(self) -> None:
        """Saves the last 20 items to a JSON file."""
        data_to_save = []
        # We only save up to the last 20 items
        count = min(self.list_widget.count(), self.MAX_HISTORY_SAVE)

        for index in range(count):
            item = self.list_widget.item(index)
            data_to_save.append({
                "text": item.data(Qt.ItemDataRole.UserRole),
                "pinned": item.data(Qt.ItemDataRole.UserRole + 1)
            })

        try:
            with open(self.STORAGE_FILE, 'w', encoding='utf-8') as file_handle:
                json.dump(data_to_save, file_handle, ensure_ascii=False, indent=4)
        except Exception as exception:
            print(f"Failed to save history: {exception}")

    def _load_history_from_disk(self) -> None:
        """Loads items from the JSON file on startup."""
        if not os.path.exists(self.STORAGE_FILE):
            return

        try:
            with open(self.STORAGE_FILE, encoding='utf-8') as file_handle:
                saved_items = json.load(file_handle)
                # Load in reverse to maintain the 'newest at top' order during insertion
                for item_data in reversed(saved_items):
                    self._add_clipboard_item(
                        item_data["text"],
                        is_pinned=item_data.get("pinned", False)
                    )
        except Exception as exception:
            print(f"Failed to load history: {exception}")

    def closeEvent(self, event) -> None:
        """Override closeEvent to ensure data is saved when app actually quits."""
        self._save_history_to_disk()
        event.accept()

    # --- UPDATED METHODS ---

    def _add_clipboard_item(self, text: str, is_pinned: bool = False) -> None:
        """Updated to support pre-pinned status from save file."""
        display_text = self._format_display_text(text)
        if is_pinned:
            display_text = f"📌 {display_text}"

        item = QListWidgetItem(display_text)
        item.setData(Qt.ItemDataRole.UserRole, text)
        item.setData(Qt.ItemDataRole.UserRole + 1, is_pinned)

        if is_pinned:
            item.setForeground(QColor("#ffcc00"))
            self.list_widget.insertItem(0, item)
        else:
            insert_pos = self._get_first_non_pinned_index()
            self.list_widget.insertItem(insert_pos, item)

        # Optional: Save every time a new item is added to be safe
        self._save_history_to_disk()

    # --- REFACTORED CORE (Matches previous version) ---

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
        """Apply dark theme styling to the application components."""
        style = """
            QWidget { background-color: #1e1e1e; }
            QLabel { color: #8e8e93; font-size: 11px; font-weight: bold; margin-left: 10px; margin-top: 5px; }
            QLineEdit { background-color: #3c3c3c; color: #ffffff; border: 1px solid #555555; border-radius: 5px; padding: 8px; margin: 5px 10px; }
            QListWidget { border: none; background-color: #252526; border-radius: 8px; margin: 5px; outline: none; }
            QListWidget::item { padding: 12px; border-bottom: 1px solid #333333; color: #d4d4d4; }
            QListWidget::item:alternate { background-color: #2d2d2d; }
            QListWidget::item:selected { background-color: #094771; color: white; border-radius: 4px; }
        """
        self.setStyleSheet(style)

    def _setup_ui_components(self) -> None:
        """Create and arrange the main UI components including search bar, label, and list widget."""
        self.layout = QVBoxLayout()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search history...")
        self.label = QLabel("HISTORY (Double-click to Pin)")
        self.list_widget = QListWidget()
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.layout.addWidget(self.search_bar)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.list_widget)
        self.setLayout(self.layout)

    def _setup_clipboard_monitoring(self) -> None:
        """Initialize clipboard monitoring with a timer to check for changes."""
        self.clipboard = QApplication.clipboard()
        self.last_seen_text = self._get_current_clipboard_text()
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_clipboard)
        self.timer.start(self.CLIPBOARD_CHECK_INTERVAL)

    def _load_initial_clipboard(self) -> None:
        """Load the current clipboard content as the first item if it's new and not empty."""
        text = self._get_current_clipboard_text()
        if text.strip() and self._is_new_clipboard_content(text):
            self._add_clipboard_item(text)

    def _connect_signals(self) -> None:
        """Connect UI signals to their respective handler methods."""
        self.list_widget.itemClicked.connect(self._copy_item_back)
        self.list_widget.itemDoubleClicked.connect(self.toggle_pin)
        self.search_bar.textChanged.connect(self._filter_list)

    def toggle_pin(self, item) -> None:
        """Toggle the pin status of a clipboard item and reposition it accordingly.

        Args:
            item: The QListWidgetItem to toggle pin status for.
        """
        is_pinned = not item.data(Qt.ItemDataRole.UserRole + 1)
        text = item.data(Qt.ItemDataRole.UserRole)
        # Remove and re-add to handle positioning logic properly
        self.list_widget.takeItem(self.list_widget.row(item))
        self._add_clipboard_item(text, is_pinned=is_pinned)
        self._save_history_to_disk()

    def _get_first_non_pinned_index(self) -> int:
        """Find the index of the first non-pinned item in the list.

        Returns:
            int: Index where the first non-pinned item should be inserted.
        """
        for index in range(self.list_widget.count()):
            if not self.list_widget.item(index).data(Qt.ItemDataRole.UserRole + 1):
                return index
        return self.list_widget.count()

    def _filter_list(self, query: str) -> None:
        """Filter the clipboard history list based on the search query.

        Args:
            query: The search string to filter items by.
        """
        query = query.lower()
        for index in range(self.list_widget.count()):
            item = self.list_widget.item(index)
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
        """Monitor clipboard for changes and add new content to history.

        This method is called periodically by the timer to detect new clipboard content.
        """
        current_text = self._get_current_clipboard_text()
        if current_text and current_text.strip() and current_text != self.last_seen_text:
            if self._is_new_clipboard_content(current_text):
                self.last_seen_text = current_text
                self._add_clipboard_item(current_text)
                self._filter_list(self.search_bar.text())

    def _is_new_clipboard_content(self, text: str) -> bool:
        """Check if the provided text is not already in the clipboard history.

        Args:
            text: The clipboard content to check for duplicates.

        Returns:
            bool: True if the text is new, False if it already exists in history.
        """
        existing_values = [self.list_widget.item(index).data(Qt.ItemDataRole.UserRole)
                           for index in range(self.list_widget.count())]
        return text not in existing_values

    def _format_display_text(self, text) -> str:
        """Format text for display in the list widget by removing newlines and truncating if necessary.

        Args:
            text: The raw text to format for display.

        Returns:
            str: The formatted text suitable for display in the list widget.
        """
        display_text = text.replace('\n', ' ').strip()
        if len(display_text) > self.MAX_DISPLAY_LENGTH:
            display_text = display_text[:self.TRUNCATION_OFFSET] + \
                self.TRUNCATION_SUFFIX
        return display_text

    def _copy_item_back(self, item) -> None:
        """Copy the selected item's content back to the clipboard.

        Args:
            item: The QListWidgetItem containing the text to copy to clipboard.
        """
        try:
            self.timer.stop()
            text = item.data(Qt.ItemDataRole.UserRole)
            self.clipboard.setText(text)
            self.last_seen_text = text
            QTimer.singleShot(self.RESTORE_TIMER_DELAY, self.timer.start)
        except Exception:
            QTimer.singleShot(self.RESTORE_TIMER_DELAY, self.timer.start)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    manager = ClipboardManager()
    manager.show()
    sys.exit(app.exec())
