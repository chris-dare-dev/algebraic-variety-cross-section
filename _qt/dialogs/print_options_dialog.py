"""Modal print-options dialog: pick printer + sizing for an STL export.

``PrintOptionsDialog`` lets the user choose:

  * a printer preset (``QComboBox`` from ``export.build_volumes.list_presets``)
    plus a "Custom…" entry that reveals three dimension spinboxes;
  * a target size in mm (longest axis) OR a "Fit to plate" checkbox that
    disables the size spinbox and fills the build volume;
  * a build-volume margin per side (mm);
  * binary vs ASCII STL.

All the *sizing/validation* logic lives in ``export.build_volumes`` — this
dialog only collects raw inputs and forwards them to ``build_export_kwargs``.
That keeps the math Qt-free (AI-2): tests exercise the resolution path without
ever constructing a widget, and the dialog itself only needs a headless
offscreen smoke test.

Invariants honoured here:
  * AI-11 — every Qt enum is fully qualified (``Qt.AlignmentFlag.*``,
    ``QDialog.DialogCode.*``, ``QDialogButtonBox.StandardButton.*``).
  * AI-12 / AI-13 — no inline hex colours; the dialog inherits the global app
    stylesheet. Object names are set so QSS palette roles can target it.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from export.build_volumes import build_export_kwargs, list_presets

#: Sentinel combo entry that reveals the custom-dimension spinboxes.
CUSTOM_ENTRY = "Custom…"


class PrintOptionsDialog(QDialog):
    """Collect printer + sizing options for a print-ready STL export."""

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        printer: str | None = None,
        target_mm: float = 120.0,
        fit_to_plate: bool = False,
        margin_mm: float = 5.0,
        binary: bool = True,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("printOptionsDialog")
        self.setWindowTitle("Print Options")
        self.setModal(True)

        presets = list_presets()

        # --- printer preset + custom dims -------------------------------
        self._printer_combo = QComboBox()
        self._printer_combo.setObjectName("printerCombo")
        self._printer_combo.addItems(presets)
        self._printer_combo.addItem(CUSTOM_ENTRY)
        if printer and printer in presets:
            self._printer_combo.setCurrentText(printer)
        elif presets:
            self._printer_combo.setCurrentIndex(0)

        self._dim_x = self._make_dim_spin(340.0)
        self._dim_y = self._make_dim_spin(320.0)
        self._dim_z = self._make_dim_spin(340.0)
        self._dims_row = QWidget()
        self._dims_row.setObjectName("customDimsRow")
        dims_layout = QHBoxLayout(self._dims_row)
        dims_layout.setContentsMargins(0, 0, 0, 0)
        for label, spin in (("X", self._dim_x), ("Y", self._dim_y), ("Z", self._dim_z)):
            dims_layout.addWidget(QLabel(label))
            dims_layout.addWidget(spin)

        # --- size / fit-to-plate ----------------------------------------
        self._size_spin = QDoubleSpinBox()
        self._size_spin.setObjectName("sizeSpin")
        self._size_spin.setRange(1.0, 10000.0)
        self._size_spin.setDecimals(1)
        self._size_spin.setSingleStep(5.0)
        self._size_spin.setSuffix(" mm")
        self._size_spin.setValue(float(target_mm) if target_mm and target_mm > 0 else 120.0)

        self._fit_check = QCheckBox("Fit to plate (fill the build volume)")
        self._fit_check.setObjectName("fitToPlateCheck")
        self._fit_check.setChecked(bool(fit_to_plate))

        # --- margin -----------------------------------------------------
        self._margin_spin = QDoubleSpinBox()
        self._margin_spin.setObjectName("marginSpin")
        self._margin_spin.setRange(0.0, 100.0)
        self._margin_spin.setDecimals(1)
        self._margin_spin.setSingleStep(1.0)
        self._margin_spin.setSuffix(" mm")
        self._margin_spin.setValue(float(margin_mm))

        # --- binary / ascii ---------------------------------------------
        self._format_combo = QComboBox()
        self._format_combo.setObjectName("stlFormatCombo")
        self._format_combo.addItems(["Binary STL (smaller)", "ASCII STL"])
        self._format_combo.setCurrentIndex(0 if binary else 1)

        # --- layout -----------------------------------------------------
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.addRow("Printer:", self._printer_combo)
        form.addRow("Build volume:", self._dims_row)
        form.addRow("Target size:", self._size_spin)
        form.addRow("", self._fit_check)
        form.addRow("Margin/side:", self._margin_spin)
        form.addRow("Format:", self._format_combo)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        root = QVBoxLayout(self)
        root.addLayout(form)
        root.addWidget(buttons)

        # --- wiring -----------------------------------------------------
        self._printer_combo.currentTextChanged.connect(self._sync_custom_dims)
        self._fit_check.toggled.connect(self._sync_fit_to_plate)

        self._sync_custom_dims()
        self._sync_fit_to_plate()

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _make_dim_spin(default: float) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(1.0, 10000.0)
        spin.setDecimals(0)
        spin.setSingleStep(10.0)
        spin.setSuffix(" mm")
        spin.setValue(default)
        return spin

    def _is_custom(self) -> bool:
        return self._printer_combo.currentText() == CUSTOM_ENTRY

    def _sync_custom_dims(self) -> None:
        """Show the dimension spinboxes only for the Custom… entry."""
        self._dims_row.setVisible(self._is_custom())

    def _sync_fit_to_plate(self) -> None:
        """Disable the size spinbox while Fit-to-plate is checked."""
        self._size_spin.setEnabled(not self._fit_check.isChecked())

    # ------------------------------------------------------------------
    # results
    # ------------------------------------------------------------------
    def options(self) -> dict:
        """Return the chosen raw inputs (printer/dims/target/fit/margin/binary).

        This is the un-resolved view — handy for persistence. Use
        :meth:`export_kwargs` to get the ``export_to_stl`` keyword dict.
        """
        custom = self._is_custom()
        return {
            "printer": None if custom else self._printer_combo.currentText(),
            "dims": (
                (self._dim_x.value(), self._dim_y.value(), self._dim_z.value())
                if custom
                else None
            ),
            "target_mm": self._size_spin.value(),
            "fit_to_plate": self._fit_check.isChecked(),
            "margin_mm": self._margin_spin.value(),
            "binary": self._format_combo.currentIndex() == 0,
        }

    def export_kwargs(self) -> dict:
        """Resolve the chosen options into ``export_to_stl`` keyword arguments.

        Delegates ALL validation to ``export.build_volumes.build_export_kwargs``
        (Qt-free) so the dialog carries no sizing logic of its own.
        """
        opts = self.options()
        return build_export_kwargs(
            printer=opts["printer"],
            dims=opts["dims"],
            target_mm=(None if opts["fit_to_plate"] else opts["target_mm"]),
            fit_to_plate=opts["fit_to_plate"],
            margin_mm=opts["margin_mm"],
            binary=opts["binary"],
        )
