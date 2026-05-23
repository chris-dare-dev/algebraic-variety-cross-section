"""Regression guards for the Double-pass-smooth auto-disable
acknowledgment toast.

hq-disable-toast-2026q3-e1 (F-L2 closure from enriques-hq-smoothing-
2026q3-e1): when the user switches variety or subtype while
Double-pass smooth is enabled and the new variety/subtype takes it
out of scope, ``set_hq_smoothing_eligible(False)`` silently clears
the toggle via the ``blockSignals`` programmatic-reset pattern.
This milestone surfaces a one-shot ``statusBar().showMessage``
acknowledgment so the user understands WHY the toggle was auto-
disabled (per-subtype scope: only Enriques figs 1+2 carry the
double-curve topology the second Taubin pass targets, per
CONTEXT.md §8.13).

All tests are pure source-text greps on ``app.py`` (AI-2 / AI-3
compliant — no ``QApplication``, no ``MainWindow()``, no live
``statusBar`` mutation).

The toast must fire at BOTH ``_on_variety_changed`` AND
``_on_subtype_changed`` — variety-only would miss the Enriques
Fig.1 → Fig.3 transition (which is a subtype-only change).
"""
from __future__ import annotations

import pathlib


_APP_SRC = (
    pathlib.Path(__file__).resolve().parent.parent / "app.py"
).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 1. Prior HQ state captured BEFORE the eligible-clear call
# ---------------------------------------------------------------------------


def test_hq_disable_toast_captures_prior_state_before_eligible_call() -> None:
    """The prior ``hq_smoothing`` state MUST be captured BEFORE
    ``set_hq_smoothing_eligible(False)`` runs.  The eligible call
    clears ``_hq_smoothing`` to False at the end of its body (the
    blockSignals + setChecked + assign pattern in
    ``appearance_panel.py``), so a read AFTER the call would always
    return False regardless of the user's actual prior state.
    """
    # The capture pattern is `_prior_hq = self.appearance_panel.hq_smoothing`.
    # It MUST appear somewhere in app.py.
    capture_pos = _APP_SRC.find(
        "_prior_hq = self.appearance_panel.hq_smoothing"
    )
    assert capture_pos != -1, (
        "app.py must capture the prior HQ state via "
        "`_prior_hq = self.appearance_panel.hq_smoothing` BEFORE the "
        "set_hq_smoothing_eligible(False) call — F-L2 closure pattern."
    )
    # The first set_hq_smoothing_eligible(...) call AFTER the capture
    # must appear, anchoring the before-the-clear ordering.
    eligible_after_capture = _APP_SRC.find(
        "self.appearance_panel.set_hq_smoothing_eligible(",
        capture_pos,
    )
    assert eligible_after_capture != -1, (
        "set_hq_smoothing_eligible call must follow the _prior_hq "
        "capture — the capture is read-once, the eligible call is the "
        "state-clearing operation, and the order matters."
    )


# ---------------------------------------------------------------------------
# 2. Conditional guard appears (only fires when prior was True)
# ---------------------------------------------------------------------------


def test_hq_disable_toast_conditional_guard_present() -> None:
    """The acknowledgment toast MUST be guarded by ``if _prior_hq`` (or
    equivalent) so it fires ONLY when the user had Double-pass smooth
    enabled before the switch.  Without the guard the toast would
    fire on every variety/subtype switch — annoying noise for the
    common case (HQ never enabled).
    """
    assert "if _prior_hq" in _APP_SRC, (
        "app.py must contain an `if _prior_hq` (or equivalent) guard — "
        "the toast must fire only when the user actually had "
        "Double-pass smooth enabled before the switch.  Empty saved "
        "state / never-enabled case stays silent."
    )


# ---------------------------------------------------------------------------
# 3. Message text explains the eligibility scope (AI-15 honesty)
# ---------------------------------------------------------------------------


def test_hq_disable_toast_message_explains_eligibility_scope() -> None:
    """The acknowledgment text MUST name what was auto-disabled AND
    explain the eligibility scope (Enriques figs 1+2 only).  Without
    the explanation the toast reads as "your setting got nuked" with
    no actionable context — AI-15 honesty requires the WHY.
    """
    assert "Double-pass smooth disabled" in _APP_SRC, (
        "Status-bar toast MUST include the literal 'Double-pass smooth "
        "disabled' — AI-15: the user-facing label was renamed from "
        "'HQ smoothing' by hq-smoothing-label-rename-2026q3-e1, and "
        "the acknowledgment text must use the current label."
    )
    # The scope explanation must reference Enriques figs 1+2 (the actual
    # eligibility frozenset).
    assert (
        "Enriques figs 1+2" in _APP_SRC
        or "Enriques fig 1" in _APP_SRC
    ), (
        "Status-bar toast MUST reference the Enriques figs 1+2 scope "
        "so the user understands WHY the auto-disable happened "
        "(per-subtype double-curve topology — CONTEXT.md §8.13)."
    )


# ---------------------------------------------------------------------------
# 4. Both call sites present (variety + subtype handlers)
# ---------------------------------------------------------------------------


def test_hq_disable_toast_fires_in_both_variety_and_subtype_handlers() -> None:
    """The toast MUST be wired at BOTH ``_on_variety_changed`` AND
    ``_on_subtype_changed`` — variety-only would miss the Enriques
    Fig.1 → Fig.3 transition (which is a subtype-only change).  The
    research brief's trigger-condition trace called this out as the
    "load-bearing dual-call-site" requirement.

    Source-grep proxy: count the ``_prior_hq`` captures — at least 2
    must exist (one per handler).
    """
    count = _APP_SRC.count(
        "_prior_hq = self.appearance_panel.hq_smoothing"
    )
    assert count >= 2, (
        f"Expected >= 2 '_prior_hq' captures (one in "
        f"_on_variety_changed, one in _on_subtype_changed) but found "
        f"{count}. The Enriques Fig.1 → Fig.3 transition is caught "
        f"ONLY by _on_subtype_changed (variety stays Enriques, only "
        f"the subtype combo fires)."
    )
    # The subtype handler's toast text differs from the variety
    # handler's — the subtype version adds "(double-curve topology)"
    # as the WHY explanation. Verify both message variants are present.
    assert "double-curve topology" in _APP_SRC, (
        "_on_subtype_changed's toast must include '(double-curve "
        "topology)' as the explanatory tail — distinguishes the "
        "subtype-only message from the variety-change message and "
        "anchors the per-figure-topology reason per CONTEXT.md §8.13."
    )
