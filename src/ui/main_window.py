from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets

from core.config import DEFAULT_MATCH_MODE, MAX_REGEX_LENGTH
from core.csv_loader import load_csv
from core.filtering import filter_items
from core.models import FilterSpec, SortSpec
from core.persistence import default_storage_path, load_entries, new_entry, save_entries
from core.regex_generator import generate_regex
from core.sorting import sort_items


class NumericItem(QtWidgets.QTableWidgetItem):
    def __init__(self, value, display: str) -> None:
        super().__init__(display)
        self.value = value

    def __lt__(self, other) -> bool:
        if isinstance(other, NumericItem):
            return self.value < other.value
        return super().__lt__(other)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PoE Stash Regex Generator")

        self.records = []
        self.filtered = []
        self.current_entries: list[str] = []
        self.saved_entries = []
        self.generation_counter = 0
        self.current_group_label = "None"

        self.storage_path = default_storage_path()

        self.filter_timer = QtCore.QTimer(self)
        self.filter_timer.setSingleShot(True)
        self.filter_timer.setInterval(250)
        self.filter_timer.timeout.connect(self._apply_filters_update_view)

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        main_layout = QtWidgets.QVBoxLayout(central)

        file_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(file_layout)

        file_layout.addWidget(QtWidgets.QLabel("CSV"))
        self.csv_path_edit = QtWidgets.QLineEdit()
        file_layout.addWidget(self.csv_path_edit)

        browse_button = QtWidgets.QPushButton("Browse")
        browse_button.clicked.connect(self._browse_csv)
        file_layout.addWidget(browse_button)

        load_button = QtWidgets.QPushButton("Load")
        load_button.clicked.connect(self._load_csv)
        file_layout.addWidget(load_button)

        filter_group = QtWidgets.QGroupBox("Filters")
        filter_layout = QtWidgets.QGridLayout(filter_group)
        main_layout.addWidget(filter_group)

        filter_layout.addWidget(QtWidgets.QLabel("Tabs (comma separated)"), 0, 0)
        self.tabs_edit = QtWidgets.QLineEdit()
        filter_layout.addWidget(self.tabs_edit, 0, 1)
        filter_layout.addWidget(QtWidgets.QLabel("Name contains"), 0, 2)
        self.name_contains_edit = QtWidgets.QLineEdit()
        self.name_contains_edit.setToolTip("Case-insensitive substring match on item names")
        filter_layout.addWidget(self.name_contains_edit, 0, 3)

        filter_layout.addWidget(QtWidgets.QLabel("Min Total"), 1, 0)
        self.min_total_edit = QtWidgets.QLineEdit()
        filter_layout.addWidget(self.min_total_edit, 1, 1)
        filter_layout.addWidget(QtWidgets.QLabel("Max Total"), 1, 2)
        self.max_total_edit = QtWidgets.QLineEdit()
        filter_layout.addWidget(self.max_total_edit, 1, 3)

        filter_layout.addWidget(QtWidgets.QLabel("Min Price"), 2, 0)
        self.min_price_edit = QtWidgets.QLineEdit()
        filter_layout.addWidget(self.min_price_edit, 2, 1)
        filter_layout.addWidget(QtWidgets.QLabel("Max Price"), 2, 2)
        self.max_price_edit = QtWidgets.QLineEdit()
        filter_layout.addWidget(self.max_price_edit, 2, 3)

        filter_layout.addWidget(QtWidgets.QLabel("Min Quantity"), 3, 0)
        self.min_quantity_edit = QtWidgets.QLineEdit()
        filter_layout.addWidget(self.min_quantity_edit, 3, 1)
        filter_layout.addWidget(QtWidgets.QLabel("Max Quantity"), 3, 2)
        self.max_quantity_edit = QtWidgets.QLineEdit()
        filter_layout.addWidget(self.max_quantity_edit, 3, 3)

        top_n_label = QtWidgets.QLabel("Top X items")
        top_n_label.setToolTip("Top X items by total value")
        filter_layout.addWidget(top_n_label, 4, 0)
        self.top_n_edit = QtWidgets.QLineEdit()
        self.top_n_edit.setToolTip("Top X items by total value")
        filter_layout.addWidget(self.top_n_edit, 4, 1)
        bottom_n_label = QtWidgets.QLabel("Bottom X items")
        bottom_n_label.setToolTip("Bottom X items by total value")
        filter_layout.addWidget(bottom_n_label, 4, 2)
        self.bottom_n_edit = QtWidgets.QLineEdit()
        self.bottom_n_edit.setToolTip("Bottom X items by total value")
        filter_layout.addWidget(self.bottom_n_edit, 4, 3)

        filter_layout.addWidget(QtWidgets.QLabel("Sort"), 0, 4)
        self.sort_field_combo = QtWidgets.QComboBox()
        self.sort_field_combo.addItems(["None", "name", "tab", "quantity", "total"])
        filter_layout.addWidget(self.sort_field_combo, 0, 5)

        filter_layout.addWidget(QtWidgets.QLabel("Order"), 1, 4)
        self.sort_order_combo = QtWidgets.QComboBox()
        self.sort_order_combo.addItems(["Ascending", "Descending"])
        filter_layout.addWidget(self.sort_order_combo, 1, 5)

        filter_layout.addWidget(QtWidgets.QLabel("Match Mode"), 3, 4)
        self.match_mode_combo = QtWidgets.QComboBox()
        self.match_mode_combo.addItem("Balanced (word suffix)", "balanced")
        self.match_mode_combo.addItem("Exact (full name)", "exact")
        self.match_mode_combo.addItem("Compact (short suffix)", "compact")
        match_index = self.match_mode_combo.findData(DEFAULT_MATCH_MODE)
        if match_index >= 0:
            self.match_mode_combo.setCurrentIndex(match_index)
        filter_layout.addWidget(self.match_mode_combo, 3, 5)

        reset_filters_button = QtWidgets.QPushButton("Reset Filters")
        reset_filters_button.clicked.connect(self._reset_filters)
        filter_layout.addWidget(reset_filters_button, 4, 5)

        generate_button = QtWidgets.QPushButton("Generate Regex")
        generate_button.clicked.connect(self._generate_regex)
        filter_layout.addWidget(generate_button, 2, 5)

        for widget in (
            self.tabs_edit,
            self.name_contains_edit,
            self.min_total_edit,
            self.max_total_edit,
            self.min_price_edit,
            self.max_price_edit,
            self.min_quantity_edit,
            self.max_quantity_edit,
            self.top_n_edit,
            self.bottom_n_edit,
        ):
            widget.textChanged.connect(self._schedule_filter_refresh)
        self.sort_field_combo.currentIndexChanged.connect(self._schedule_filter_refresh)
        self.sort_order_combo.currentIndexChanged.connect(self._schedule_filter_refresh)

        self.table = QtWidgets.QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Name", "Tab", "Quantity", "Price", "Total"])
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
        header.setSortIndicatorShown(True)
        self.table.setSortingEnabled(True)
        self.table.setColumnWidth(0, 420)
        self.table.setColumnWidth(1, 140)
        self.table.setColumnWidth(2, 110)
        self.table.setColumnWidth(3, 110)
        self.table.setColumnWidth(4, 140)
        main_layout.addWidget(self.table)

        expected_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(expected_layout)
        expected_layout.addWidget(QtWidgets.QLabel("Expected Total Value"))
        self.expected_total_value = QtWidgets.QLabel("0.00")
        expected_layout.addWidget(self.expected_total_value)
        expected_layout.addStretch()

        bottom_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(bottom_layout)

        current_group = QtWidgets.QGroupBox("Generated Regex")
        current_layout = QtWidgets.QVBoxLayout(current_group)
        bottom_layout.addWidget(current_group)

        self.current_set_label = QtWidgets.QLabel("Active Set: None")
        current_layout.addWidget(self.current_set_label)

        self.current_list = QtWidgets.QListWidget()
        self.current_list.currentRowChanged.connect(self._current_selection_changed)
        current_layout.addWidget(self.current_list)

        self.preview_edit = QtWidgets.QLineEdit()
        self.preview_edit.setReadOnly(True)
        current_layout.addWidget(self.preview_edit)

        buttons_layout = QtWidgets.QHBoxLayout()
        current_layout.addLayout(buttons_layout)

        copy_button = QtWidgets.QPushButton("Copy")
        copy_button.clicked.connect(self._copy_current)
        buttons_layout.addWidget(copy_button)

        save_button = QtWidgets.QPushButton("Save")
        save_button.clicked.connect(self._save_current)
        buttons_layout.addWidget(save_button)

        saved_group = QtWidgets.QGroupBox("Saved Regex")
        saved_layout = QtWidgets.QVBoxLayout(saved_group)
        bottom_layout.addWidget(saved_group)

        self.saved_list = QtWidgets.QListWidget()
        self.saved_list.currentRowChanged.connect(self._saved_selection_changed)
        self.saved_list.itemDoubleClicked.connect(lambda _: self._load_saved_selected())
        saved_layout.addWidget(self.saved_list)

        saved_buttons_layout = QtWidgets.QHBoxLayout()
        saved_layout.addLayout(saved_buttons_layout)

        load_saved_button = QtWidgets.QPushButton("Load Selected")
        load_saved_button.clicked.connect(self._load_saved_selected)
        saved_buttons_layout.addWidget(load_saved_button)

        delete_saved_button = QtWidgets.QPushButton("Delete Selected")
        delete_saved_button.clicked.connect(self._delete_saved_selected)
        saved_buttons_layout.addWidget(delete_saved_button)

        open_location_button = QtWidgets.QPushButton("Open Location")
        open_location_button.clicked.connect(self._open_storage_location)
        saved_buttons_layout.addWidget(open_location_button)

        self.status_bar = self.statusBar()
        self._load_saved_entries()

    def _browse_csv(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select CSV", str(Path.cwd()), "CSV Files (*.csv)")
        if path:
            self.csv_path_edit.setText(path)

    def _load_csv(self) -> None:
        path = self.csv_path_edit.text().strip()
        if not path:
            self._show_error("Please select a CSV file.")
            return

        try:
            records, warnings = load_csv(path)
        except FileNotFoundError as exc:
            self._show_error(str(exc))
            return

        self.records = records
        self._apply_filters_update_view()

        if warnings:
            self._show_warning("\n".join(warnings[:10]))

        self.status_bar.showMessage(f"Loaded {len(records)} items.")

    def _generate_regex(self) -> None:
        if not self.records:
            self._show_error("No CSV loaded.")
            return

        if not self._apply_filters_update_view(show_errors=True):
            return

        targets = [item.name for item in self.filtered]
        non_targets = self._build_non_targets(self.filtered)

        result = generate_regex(
            targets,
            non_targets,
            max_length=self._max_raw_regex_length(),
            match_mode=self._current_match_mode(),
        )
        if not result.ok:
            self._set_current_entries([], "None")
            self._show_error(result.error or "Failed to generate regex.")
            return

        self.generation_counter += 1
        group_label = f"Generated #{self.generation_counter}"
        self._set_current_entries(result.entries, group_label)
        self.status_bar.showMessage(f"Generated {len(result.entries)} entry(ies).")

    def _schedule_filter_refresh(self) -> None:
        if not self.records:
            return
        self.filter_timer.start()

    def _apply_filters_update_view(self, show_errors: bool = False) -> bool:
        if not self.records:
            self._populate_table([])
            self._update_expected_total([])
            return False

        spec, errors = self._build_filter_spec()
        if errors:
            message = "; ".join(errors)
            if show_errors:
                self._show_error(message)
                return False
            self.status_bar.showMessage(message)

        filtered = filter_items(self.records, spec)
        sort_field = self.sort_field_combo.currentText()
        if sort_field != "None":
            ascending = self.sort_order_combo.currentText() == "Ascending"
            filtered = sort_items(filtered, SortSpec(field=sort_field, ascending=ascending))

        self.filtered = filtered
        self._populate_table(filtered)
        self._update_expected_total(filtered)
        return True

    def _build_filter_spec(self) -> tuple[FilterSpec, list[str]]:
        errors: list[str] = []

        min_total, error = self._try_parse_decimal(self.min_total_edit.text())
        if error:
            errors.append(error)

        max_total, error = self._try_parse_decimal(self.max_total_edit.text())
        if error:
            errors.append(error)

        min_price, error = self._try_parse_decimal(self.min_price_edit.text())
        if error:
            errors.append(error)

        max_price, error = self._try_parse_decimal(self.max_price_edit.text())
        if error:
            errors.append(error)

        min_quantity, error = self._try_parse_int(self.min_quantity_edit.text())
        if error:
            errors.append(error)

        max_quantity, error = self._try_parse_int(self.max_quantity_edit.text())
        if error:
            errors.append(error)

        top_n, error = self._try_parse_int(self.top_n_edit.text())
        if error:
            errors.append(error)

        bottom_n, error = self._try_parse_int(self.bottom_n_edit.text())
        if error:
            errors.append(error)

        if top_n is not None and bottom_n is not None:
            errors.append("Top X and Bottom X cannot be used together.")

        if min_total is not None and max_total is not None and min_total > max_total:
            errors.append("Min Total cannot be greater than Max Total.")

        if min_price is not None and max_price is not None and min_price > max_price:
            errors.append("Min Price cannot be greater than Max Price.")

        if min_quantity is not None and max_quantity is not None and min_quantity > max_quantity:
            errors.append("Min Quantity cannot be greater than Max Quantity.")

        spec = FilterSpec(
            tabs=self._parse_tabs(self.tabs_edit.text()),
            name_query=self.name_contains_edit.text().strip() or None,
            min_total=min_total,
            max_total=max_total,
            min_price=min_price,
            max_price=max_price,
            min_quantity=min_quantity,
            max_quantity=max_quantity,
            top_n=top_n,
            bottom_n=bottom_n,
        )
        return spec, errors

    def _build_non_targets(self, selected_items) -> list[str]:
        selected_ids = {id(item) for item in selected_items}
        return [item.name for item in self.records if id(item) not in selected_ids]

    def _set_current_entries(self, entries: list[str], group_label: str) -> None:
        self.current_entries = list(entries)
        self.current_group_label = group_label
        self.current_set_label.setText(f"Active Set: {group_label}")
        self._populate_entries(entries, group_label)

    def _populate_table(self, items) -> None:
        sorting_enabled = self.table.isSortingEnabled()
        self.table.setSortingEnabled(False)

        self.table.setRowCount(len(items))
        for row_index, item in enumerate(items):
            price = self._calculate_price(item.total, item.quantity)
            self.table.setItem(row_index, 0, QtWidgets.QTableWidgetItem(item.name))
            self.table.setItem(row_index, 1, QtWidgets.QTableWidgetItem(item.tab))
            self.table.setItem(row_index, 2, NumericItem(item.quantity, str(item.quantity)))
            self.table.setItem(row_index, 3, NumericItem(price, self._format_decimal(price)))
            self.table.setItem(row_index, 4, NumericItem(item.total, self._format_decimal(item.total)))

        self.table.setSortingEnabled(sorting_enabled)

    def _populate_entries(self, entries: list[str], group_label: str) -> None:
        self.current_list.clear()
        total = len(entries)

        for index, entry in enumerate(entries, start=1):
            quoted = self._quote_regex(entry)
            if total > 1:
                display = f"{group_label} | Part {index}/{total}: {quoted}"
            else:
                display = f"{group_label}: {quoted}"
            item = QtWidgets.QListWidgetItem(display)
            item.setData(QtCore.Qt.UserRole, entry)
            item.setToolTip(quoted)
            self.current_list.addItem(item)

        if entries:
            self.current_list.setCurrentRow(0)
        else:
            self.preview_edit.clear()

    def _update_expected_total(self, items) -> None:
        total = Decimal("0")
        for item in items:
            total += item.total
        self.expected_total_value.setText(self._format_decimal(total))

    def _current_selection_changed(self, row: int) -> None:
        item = self.current_list.item(row)
        if not item:
            self.preview_edit.clear()
            return
        entry = item.data(QtCore.Qt.UserRole)
        if not entry:
            self.preview_edit.clear()
            return
        self.preview_edit.setText(self._quote_regex(entry))

    def _copy_current(self) -> None:
        item = self.current_list.currentItem()
        if not item:
            self._show_error("Select a regex entry to copy.")
            return
        entry = item.data(QtCore.Qt.UserRole)
        if not entry:
            self._show_error("Selected entry is empty.")
            return
        QtWidgets.QApplication.clipboard().setText(self._quote_regex(entry))
        self.status_bar.showMessage("Copied regex to clipboard.")

    def _save_current(self) -> None:
        if not self.current_entries:
            self._show_error("No regex entries to save.")
            return

        default_label = self._default_label()
        label, ok = QtWidgets.QInputDialog.getText(
            self,
            "Save Regex",
            "Label",
            QtWidgets.QLineEdit.Normal,
            default_label,
        )
        if not ok:
            return
        label = label.strip() or default_label

        metadata = {
            "tabs": sorted(self._parse_tabs(self.tabs_edit.text())),
            "name_query": self.name_contains_edit.text().strip() or None,
            "min_total": self.min_total_edit.text().strip() or None,
            "max_total": self.max_total_edit.text().strip() or None,
            "min_price": self.min_price_edit.text().strip() or None,
            "max_price": self.max_price_edit.text().strip() or None,
            "min_quantity": self.min_quantity_edit.text().strip() or None,
            "max_quantity": self.max_quantity_edit.text().strip() or None,
            "top_n": self.top_n_edit.text().strip() or None,
            "bottom_n": self.bottom_n_edit.text().strip() or None,
            "match_mode": self._current_match_mode(),
        }
        entry = new_entry(label, list(self.current_entries), metadata)
        self.saved_entries.append(entry)
        save_entries(self.storage_path, self.saved_entries)
        self._refresh_saved_list()
        self.status_bar.showMessage("Saved regex entry.")

    def _default_label(self) -> str:
        tabs = ",".join(sorted(self._parse_tabs(self.tabs_edit.text()))) or "all"
        name_query = self.name_contains_edit.text().strip()
        min_total = self.min_total_edit.text().strip()
        max_total = self.max_total_edit.text().strip()
        min_price = self.min_price_edit.text().strip()
        max_price = self.max_price_edit.text().strip()
        min_quantity = self.min_quantity_edit.text().strip()
        max_quantity = self.max_quantity_edit.text().strip()
        top_n = self.top_n_edit.text().strip()
        bottom_n = self.bottom_n_edit.text().strip()

        parts = [f"T={tabs}"]
        if name_query:
            parts.append(f"Name~{name_query}")
        if min_total:
            parts.append(f"MinT={min_total}")
        if max_total:
            parts.append(f"MaxT={max_total}")
        if min_price:
            parts.append(f"MinP={min_price}")
        if max_price:
            parts.append(f"MaxP={max_price}")
        if min_quantity:
            parts.append(f"MinQ={min_quantity}")
        if max_quantity:
            parts.append(f"MaxQ={max_quantity}")
        if top_n:
            parts.append(f"Top={top_n}")
        if bottom_n:
            parts.append(f"Bot={bottom_n}")

        return " | ".join(parts)

    def _current_match_mode(self) -> str:
        data = self.match_mode_combo.currentData()
        return data if data else DEFAULT_MATCH_MODE

    def _reset_filters(self) -> None:
        fields = [
            self.tabs_edit,
            self.name_contains_edit,
            self.min_total_edit,
            self.max_total_edit,
            self.min_price_edit,
            self.max_price_edit,
            self.min_quantity_edit,
            self.max_quantity_edit,
            self.top_n_edit,
            self.bottom_n_edit,
        ]

        for field in fields:
            field.blockSignals(True)
            field.clear()
            field.blockSignals(False)

        self.filter_timer.stop()
        self._apply_filters_update_view()

    def _load_saved_entries(self) -> None:
        entries, warnings = load_entries(self.storage_path)
        self.saved_entries = entries
        self._refresh_saved_list()
        if warnings:
            self._show_warning("\n".join(warnings))

    def _refresh_saved_list(self) -> None:
        self.saved_list.clear()
        for entry in self.saved_entries:
            self.saved_list.addItem(entry.label)

    def _saved_selection_changed(self, row: int) -> None:
        if row < 0 or row >= len(self.saved_entries):
            return
        entry = self.saved_entries[row]
        self.status_bar.showMessage(f"Selected saved regex: {entry.label}")

    def _load_saved_selected(self) -> None:
        row = self.saved_list.currentRow()
        if row < 0 or row >= len(self.saved_entries):
            self._show_error("Select a saved regex entry to load.")
            return
        entry = self.saved_entries[row]
        self._set_current_entries(list(entry.entries), f"Saved: {entry.label}")
        self.status_bar.showMessage(f"Loaded saved regex: {entry.label}")

    def _delete_saved_selected(self) -> None:
        row = self.saved_list.currentRow()
        if row < 0 or row >= len(self.saved_entries):
            self._show_error("Select a saved regex entry to delete.")
            return

        entry = self.saved_entries[row]
        confirm = QtWidgets.QMessageBox.question(
            self,
            "Delete Saved Regex",
            f"Delete '{entry.label}'?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No,
        )
        if confirm != QtWidgets.QMessageBox.Yes:
            return

        del self.saved_entries[row]
        save_entries(self.storage_path, self.saved_entries)
        self._refresh_saved_list()

        if self.current_group_label == f"Saved: {entry.label}":
            self._set_current_entries([], "None")

        self.status_bar.showMessage(f"Deleted saved regex: {entry.label}")

    def _open_storage_location(self) -> None:
        storage_path = Path(self.storage_path)
        folder = storage_path.parent
        url = QtCore.QUrl.fromLocalFile(str(folder))
        if not QtGui.QDesktopServices.openUrl(url):
            self._show_error("Unable to open the storage folder.")

    @staticmethod
    def _try_parse_decimal(value: str) -> tuple[Optional[Decimal], Optional[str]]:
        text = value.strip()
        if not text:
            return None, None
        try:
            return Decimal(text), None
        except (InvalidOperation, ValueError):
            return None, f"Invalid decimal value: {value}"

    @staticmethod
    def _try_parse_int(value: str) -> tuple[Optional[int], Optional[str]]:
        text = value.strip()
        if not text:
            return None, None
        try:
            return int(text), None
        except ValueError:
            return None, f"Invalid integer value: {value}"

    @staticmethod
    def _parse_tabs(value: str) -> set[str]:
        if not value.strip():
            return set()
        return {tab.strip() for tab in value.split(",") if tab.strip()}

    @staticmethod
    def _format_decimal(value: Decimal) -> str:
        rounded = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return str(rounded)

    @staticmethod
    def _calculate_price(total: Decimal, quantity: int) -> Decimal:
        if quantity <= 0:
            return Decimal("0")
        return (total / Decimal(quantity)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def _quote_regex(regex: str) -> str:
        return f'"{regex}"'

    @staticmethod
    def _max_raw_regex_length() -> int:
        return max(1, MAX_REGEX_LENGTH - 2)

    def _show_error(self, message: str) -> None:
        QtWidgets.QMessageBox.critical(self, "Error", message)

    def _show_warning(self, message: str) -> None:
        QtWidgets.QMessageBox.warning(self, "Warning", message)
