# Copyright 2018 Timothy M. Shead
#
# This file is part of Buildcat.
#
# Buildcat is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Buildcat is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Buildcat.  If not, see <http://www.gnu.org/licenses/>.

"""Objects that control the build process.

:class:`buildcat.build.Outdated` provides the default logic for determining
when a target needs to be rebuilt: in a nutshell, it rebuilds a target if it
doesn't exist, or if it's older than any of its dependencies.  In some cases
you might want to use :class:`buildcat.build.Nonexistent`, which only builds a
target if it doesn't exist - later updates to its dependencies will be ignored.
You might occasionally use :class:`buildcat.build.Always`, which always
unconditionally rebuilds a target, whether it already exists or not.  You use
these classes by passing them to :meth:`buildcat.process.Process.add_action` as
you define your build process.

If you need some other, more complex logic, you can implement it by deriving
your own class from :class:`buildcat.build.Criteria` and implementing the
:meth:`buildcat.build.Criteria.outdated` method.
"""

from __future__ import absolute_import, division, print_function

import abc
import logging
import os

import custom_inherit
import six

log = logging.getLogger(__name__)


@six.add_metaclass(custom_inherit.DocInheritMeta(abstract_base_class=True, style="numpy_napoleon"))
class Criteria(object):
    """Abstract base class for build criteria that determine when a :ref:`target <targets>` is out-of-date and needs to be built."""
    def __init__(self):
        pass

    def __repr__(self):
        return "buildcat.build.Criteria()"

    @abc.abstractmethod
    def outdated(self, environment, inputs, outputs):
        """Return `True` if any of the given `outputs` is out-of-date and needs to be built.

        Parameters
        ----------
        inputs: sequence of :class:`buildcat.target.Target` instances, required.
            Zero-to-many dependencies of the given `outputs`.
        outputs: sequence of :class:`buildcat.target.Target` instances, required.
            One-to-many targets to be tested for freshness.
        """
        raise NotImplementedError()


class Always(Criteria):
    """Build criteria that always considers every target out-of-date, forcing an unconditional rebuild."""
    def __init__(self):
        super(Always, self).__init__()

    def __repr__(self):
        return "buildcat.build.Always()"

    def outdated(self, environment, inputs, outputs):
        return True


class Never(Criteria):
    """Build criteria that never considers a target out-of-date, even if it doesn't exist or is older than its dependencies.

    Useful only for testing.
    """
    def __init__(self):
        super(Never, self).__init__()

    def __repr__(self):
        return "buildcat.build.Never()"

    def outdated(self, environment, inputs, outputs):
        return False


class Nonexistent(Criteria):
    """Build criteria that builds a target **only** if it doesn't exist.

    Note that this criteria ignores whether a target is older than its dependencies.
    """
    def __init__(self):
        super(Nonexistent, self).__init__()

    def __repr__(self):
        return "buildcat.build.Nonexistent()"

    def outdated(self, environment, inputs, outputs):
        for node in outputs:
            if not node.exists(environment):
                return True
        return False


class Outdated(Criteria):
    """Default build criteria that builds a target if it doesn't exist, or it's older than any of its dependencies."""
    def __init__(self):
        super(Outdated, self).__init__()

    def __repr__(self):
        return "buildcat.build.Outdated()"

    def outdated(self, environment, inputs, outputs):
        for node in outputs:
            if not node.exists(environment):
                return True

            output_timestamp = node.timestamp(environment)
            if output_timestamp is None:
                return True

            for inode in inputs:
                input_timestamp = node.timestamp(environment)
                if input_timestamp is None:
                    return True

                if input_timestamp > output_timestamp:
                    return True

        return False
