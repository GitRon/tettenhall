"""
The CSS classes the crispy FormHelper layouts hang on their fields and buttons.

They sit here rather than at the sixteen call sites because they are one vocabulary with six callers,
and because the identity is one table to edit rather than sixteen inline strings. What the values may
say is docs/patterns/visual-identity.md.

Utilities that set the same property are never stacked. Which of two competing classes wins is decided
by their order in the compiled stylesheet, not by their order in the attribute, so "h-10 h-[30px]" is a
coin toss - the small button therefore starts from its own base rather than overriding the medium one.
"""

# The box every text input and dropdown draws. Padding is split out because a select is not padded
# symmetrically, and "px-*" plus a "pr-*" on top would be exactly the coin toss described above.
#
# "py-0" clears the 1px the browser puts on an input of its own, and "box-border" keeps a bordered
# control inside the width it was given rather than 22px wider than its column.
_CONTROL = "box-border w-full border border-rule bg-ground py-0 text-base text-ink"

INPUT = f"{_CONTROL} h-10 px-2.5"
SELECT = f"{_CONTROL} h-10 pl-2.5 pr-5"

#: A dropdown that takes several warriors at once.
#:
#: The same box without the height: a "multiple" select sizes itself to show a handful of its options,
#: and a fixed 40px leaves the player picking a war band through a one-line slot.
SELECT_MULTIPLE = f"{_CONTROL} pl-2.5 pr-5"

#: The gap between one labelled field and the next.
FIELD_SPACING = "mb-5"

#: A fieldset carries the browser's own margin, padding and border, and the layouts want none of them.
FIELDSET = "m-0 border-0 p-0"

_BUTTON = "box-border inline-block cursor-pointer border py-0 font-display text-sm uppercase tracking-[0.06em]"
_BUTTON_MEDIUM = f"{_BUTTON} h-10 px-[30px]"
_BUTTON_SMALL = f"{_BUTTON} h-[30px] px-[15px]"

# Every variant answers the pointer by moving its background. A button that does not answer reads as
# disabled, and the palette has no second shade of anything to answer with.
#
# The filled treatment is the same string twice on purpose. There is one reserved colour, and a form
# whose only button commits the player to something - signing in, taking a contract, marching on a
# rival - is exactly what it is reserved for, whether or not the wording sounds dangerous. Both names
# survive because the call sites read better for saying which they meant.
_FILLED = "border-blood bg-blood text-ground hover:bg-raised hover:text-ink"
_PRIMARY = _FILLED
_DANGER = _FILLED
_DEFAULT = "border-rule bg-transparent text-ink hover:bg-raised"

BUTTON_PRIMARY = f"{_BUTTON_MEDIUM} {_PRIMARY}"
BUTTON_PRIMARY_SMALL = f"{_BUTTON_SMALL} {_PRIMARY}"
BUTTON_DANGER_SMALL = f"{_BUTTON_SMALL} {_DANGER}"
BUTTON_DEFAULT_SMALL = f"{_BUTTON_SMALL} {_DEFAULT}"
