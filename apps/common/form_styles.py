"""
The CSS classes the crispy FormHelper layouts hang on their fields and buttons.

They sit here rather than at the sixteen call sites because they are one vocabulary with six callers,
and because #64 replaces the values wholesale once there is a palette: a table is one edit, sixteen
inline strings are sixteen.

Utilities that set the same property are never stacked. Which of two competing classes wins is decided
by their order in the compiled stylesheet, not by their order in the attribute, so "h-10 h-[30px]" is a
coin toss - the small button therefore starts from its own base rather than overriding the medium one.
"""

# The box every text input and dropdown draws. Padding is split out because a select is not padded
# symmetrically, and "px-*" plus a "pr-*" on top would be exactly the coin toss described above.
#
# "box-border" and "py-0" are doing real work rather than tidying. Nothing sets "box-sizing" globally -
# Tailwind's preflight is the usual source and it stays switched off until #200 - so a control is
# "content-box" and lays its border and padding outside the width it was given: "w-full" then comes out
# 22px wider than the column it sits in. "py-0" clears the 1px the browser puts on an input of its own.
_CONTROL = "box-border w-full border border-[#e5e5e5] bg-white py-0 text-base text-[#666]"

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

_BUTTON = "box-border inline-block cursor-pointer border py-0 text-sm uppercase"
_BUTTON_MEDIUM = f"{_BUTTON} h-10 px-[30px]"
_BUTTON_SMALL = f"{_BUTTON} h-[30px] px-[15px]"

# Each variant carries its hover shade. A button that does not answer the pointer reads as disabled.
_PRIMARY = "border-transparent bg-[#1e87f0] text-white hover:bg-[#0f7ae5]"
_DANGER = "border-transparent bg-[#f0506e] text-white hover:bg-[#ee395b]"
_DEFAULT = "border-[#e5e5e5] bg-transparent text-[#333] hover:border-[#b2b2b2]"

BUTTON_PRIMARY = f"{_BUTTON_MEDIUM} {_PRIMARY}"
BUTTON_PRIMARY_SMALL = f"{_BUTTON_SMALL} {_PRIMARY}"
BUTTON_DANGER_SMALL = f"{_BUTTON_SMALL} {_DANGER}"
BUTTON_DEFAULT_SMALL = f"{_BUTTON_SMALL} {_DEFAULT}"
