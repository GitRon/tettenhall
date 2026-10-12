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

# The filled treatment is the one reserved colour, and a form whose only button commits the player to
# something - signing in, taking a contract, marching on a rival - is exactly what it is reserved for,
# whether or not the wording sounds dangerous. "DANGER" is a name of its own because the call sites read
# better for saying which they meant. The look is the "button-primary" utility in the stylesheet, which
# the templates that draw the control by hand use as well.
BUTTON_PRIMARY = "button-primary"
BUTTON_PRIMARY_SMALL = "button-primary-small"
BUTTON_DANGER_SMALL = BUTTON_PRIMARY_SMALL

#: The outlined control beside a form's filled one is the row action every template uses, defined once in
#: the stylesheet - see "The row action" in docs/patterns/visual-identity.md.
BUTTON_DEFAULT_SMALL = "row-action"
