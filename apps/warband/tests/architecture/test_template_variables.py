"""
Every template a test renders fails that test when it reads a variable that does not resolve.

Django prints an unresolved variable as nothing, which is exactly how a renamed attribute looks on the
page, so "FAIL_INVALID_TEMPLATE_VARS" in pyproject.toml turns it into a failure instead. pytest only
warns about an ini key it does not know, so a misspelt key would switch the check off without a single
test going red - this one does.

See docs/patterns/testing-strategy.md.
"""

import pytest
from django.template import Context, Template


def test_an_unresolved_template_variable_fails_the_test():
    with pytest.raises(pytest.fail.Exception, match=r"Undefined template variable 'warrior.avatar_url'"):
        Template("{{ warrior.avatar_url }}").render(Context({"warrior": object()}))
