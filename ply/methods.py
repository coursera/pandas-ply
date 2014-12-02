"""This module contains the **pandas-ply** methods which are designed to be
added to panda objects. The methods in this module should not be used directly.
Instead, the function `install_ply` should be used to attach them to the pandas
classes."""

from . import symbolic
from .vendor.six import iteritems
from .vendor.six.moves import reduce

pandas = None


def install_ply(pandas_to_use):
    """Install `pandas-ply` onto the objects in a copy of `pandas`."""

    global pandas
    pandas = pandas_to_use

    pandas.DataFrame.ply_where = _ply_where
    pandas.DataFrame.ply_select = _ply_select

    pandas.Series.ply_where = _ply_where

    pandas.core.groupby.DataFrameGroupBy.ply_select = _ply_select_for_groups

    pandas.core.groupby.SeriesGroupBy.ply_select = _ply_select_for_groups


def _ply_where(self, *conditions):
    """Filter a dataframe/series to only include rows/entries satisfying a
    given set of conditions.

    Analogous to SQL's ``WHERE``, or dplyr's ``filter``.

    Args:
        `*conditions`: Each should be a dataframe/series of booleans, a
            function returning such an object when run on the input dataframe,
            or a symbolic expression yielding such an object when evaluated
            with Symbol(0) mapped to the input dataframe. The input dataframe
            will be filtered by the AND of all the conditions.

    Example:
        >>> flights.ply_where(X.month == 1, X.day == 1)
        [ same result as `flights[(flights.month == 1) & (flights.day == 1)]` ]
    """

    if not conditions:
        return self

    evalled_conditions = [symbolic.to_callable(condition)(self)
                          for condition in conditions]
    anded_evalled_conditions = reduce(
        lambda x, y: x & y, evalled_conditions)
    return self[anded_evalled_conditions]


def _ply_select(self, *args, **kwargs):
    """Transform a dataframe by selecting old columns and new (computed)
    columns.

    Analogous to SQL's ``SELECT``, or dplyr's ``select`` / ``rename`` /
    ``mutate`` / ``transmute``.

    Args:
        `*args`: Each should be one of:

            ``'*'``
                says that all columns in the input dataframe should be
                included
            ``'column_name'``
                says that `column_name` in the input dataframe should be
                included
            ``'-column_name'``
                says that `column_name` in the input dataframe should be
                excluded.

            If any `'-column_name'` is present, then `'*'` should be
            present, and if `'*'` is present, no 'column_name' should be
            present. Column-includes and column-excludes should not overlap.
        `**kwargs`: Each argument name will be the name of a new column in the
            output dataframe, with the column's contents determined by the
            argument contents. These contents can be given as a dataframe, a
            function (taking the input dataframe as its single argument), or a
            symbolic expression (taking the input dataframe as ``Symbol(0)``).
            kwarg-provided columns override arg-provided columns.

    Example:
        >>> flights.ply_select('*',
        ...     gain = X.arr_delay - X.dep_delay,
        ...     speed = X.distance / X.air_time * 60)
        [ original dataframe, with two new computed columns added ]
    """

    input_columns = set(self.columns)

    has_star = False
    include_columns = []
    exclude_columns = []
    for arg in args:
        if arg == '*':
            if has_star:
                raise ValueError('ply_select received repeated stars')
            has_star = True
        elif arg in input_columns:
            if arg in include_columns:
                raise ValueError(
                    'ply_select received a repeated column-include (%s)' %
                    arg)
            include_columns.append(arg)
        elif arg[0] == '-' and arg[1:] in input_columns:
            if arg in exclude_columns:
                raise ValueError(
                    'ply_select received a repeated column-exclude (%s)' %
                    arg[1:])
            exclude_columns.append(arg[1:])
        else:
            raise ValueError(
                'ply_select received a strange argument (%s)' %
                arg)
    if exclude_columns and not has_star:
        raise ValueError(
            'ply_select received column-excludes without an star')
    if has_star and include_columns:
        raise ValueError(
            'ply_select received both an star and column-includes')
    if set(include_columns) & set(exclude_columns):
        raise ValueError(
            'ply_select received overlapping column-includes and ' +
            'column-excludes')

    include_columns_inc_star = self.columns if has_star else include_columns

    output_columns = [col for col in include_columns_inc_star
                      if col not in exclude_columns]

    # Note: This maintains self's index even if output_columns is [].
    to_return = self[output_columns]

    # Temporarily disable SettingWithCopyWarning, as setting columns on a
    # copy (`to_return`) is intended here.
    old_chained_assignment = pandas.options.mode.chained_assignment
    pandas.options.mode.chained_assignment = None

    for column_name, column_value in iteritems(kwargs):
        evaluated_value = symbolic.to_callable(column_value)(self)
        # TODO: verify that evaluated_value is a series!
        if column_name == 'index':
            to_return.index = evaluated_value
        else:
            to_return[column_name] = evaluated_value

    pandas.options.mode.chained_assignment = old_chained_assignment

    return to_return


# TODO: Ensure that an empty ply_select on a groupby returns a large dataframe
def _ply_select_for_groups(self, **kwargs):
    """Summarize a grouped dataframe or series.

    Analogous to SQL's ``SELECT`` (when a ``GROUP BY`` is present), or dplyr's
    ``summarise``.

    Args:
        `**kwargs`: Each argument name will be the name of a new column in the
            output dataframe, with the column's contents determined by the
            argument contents. These contents can be given as a dataframe, a
            function (taking the input grouped dataframe as its single
            argument), or a symbolic expression (taking the input grouped
            dataframe as `Symbol(0)`).
    """

    to_return = pandas.DataFrame()

    for column_name, column_value in iteritems(kwargs):
        evaluated_value = symbolic.to_callable(column_value)(self)
        if column_name == 'index':
            to_return.index = evaluated_value
        else:
            to_return[column_name] = evaluated_value

    return to_return


class PlyDataFrame:
    """The following methods are added to `pandas.DataFrame`:"""

    ply_where = _ply_where
    ply_select = _ply_select


class PlySeries:
    """The following methods are added to `pandas.Series`:"""

    ply_where = _ply_where


class PlyDataFrameGroupBy:
    """The following methods are added to
    `pandas.core.groupby.DataFrameGroupBy`:"""

    ply_select = _ply_select_for_groups


class PlySeriesGroupBy:
    """The following methods are added to
    `pandas.core.groupby.SeriesGroupBy`:"""

    ply_select = _ply_select_for_groups
