# Copyright Kevin Deldycke <kevin@deldycke.com> and contributors.
# All Rights Reserved.
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

"""Helpers and utilities for Sphinx rendering of CLI based on click-extra."""

from __future__ import annotations

# XXX Compatibility workaround because of https://github.com/pallets/pallets-sphinx-themes/blob/7b69241f1fde3cc3849f513a9dd83fa8a2f36603/src/pallets_sphinx_themes/themes/click/domain.py#L9
# Source:
# https://github.com/pallets/click/blob/dc918b48fb9006be683a684b42cc7496ad649b83/docs/conf.py#L6-L7
import click

setattr(click._compat, "text_type", str)

from pallets_sphinx_themes.themes.click import domain
from sphinx.highlighting import PygmentsBridge

from .pygments import AnsiHtmlFormatter


def setup_ansi_pygment_styles(app):
    """Add support for ANSI Shell Session syntax highlighting."""
    app.config.pygments_style = "ansi-click-extra-furo-style"
    PygmentsBridge.html_formatter = AnsiHtmlFormatter  # type: ignore


def setup(app):
    """Add support for ``.. click:example::`` and ``.. click:run::`` directives."""
    setup_ansi_pygment_styles(app)

    ####################################
    #  pallets_sphinx_themes Patch #1  #
    ####################################
    append_orig = domain.ViewList.append

    def patched_append(*args, **kwargs):
        """Replace the code block produced by ``.. click:run::`` directive with an ANSI
        Shell Session (``.. code-block:: ansi-shell-session``).

        Targets:
        - [``.. sourcecode:: text`` for `Pallets-Sphinx-Themes <= 2.0.2`](https://github.com/pallets/pallets-sphinx-themes/blob/7b69241f1fde3cc3849f513a9dd83fa8a2f36603/src/pallets_sphinx_themes/themes/click/domain.py#L245)
        - [``.. sourcecode:: shell-session`` for `Pallets-Sphinx-Themes > 2.0.2`](https://github.com/pallets/pallets-sphinx-themes/pull/62)
        """
        default_run_blocks = (
            ".. sourcecode:: text",
            ".. sourcecode:: shell-session",
        )
        for run_block in default_run_blocks:
            if run_block in args:
                args = list(args)
                index = args.index(run_block)
                args[index] = ".. code-block:: ansi-shell-session"

        return append_orig(*args, **kwargs)

    domain.ViewList.append = patched_append

    ####################################
    #  pallets_sphinx_themes Patch #2  #
    ####################################

    # Replace the call to default ``CliRunner.invoke`` with a call to click_extra own version which is sensible to contextual color settings
    # and output unfiltered ANSI codes.
    # Fixes: <insert upstream bug report here>
    from click_extra.tests.conftest import ExtraCliRunner

    # Force color rendering in ``invoke`` calls.
    ExtraCliRunner.force_color = True

    # Brutal, but effective.
    # Alternative patching methods: https://stackoverflow.com/a/38928265
    domain.ExampleRunner.__bases__ = (ExtraCliRunner,)

    # Register directives to Sphinx.
    domain.setup(app)
