import sys
if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest

from pandas.util.testing import assert_frame_equal
from pandas.util.testing import assert_series_equal
from pandas_ply.methods import install_ply
from pandas_ply.symbolic import X
import pandas as pd

install_ply(pd)


def assert_frame_equiv(df1, df2, **kwargs):
    """ Assert that two dataframes are equal, ignoring ordering of columns.

    See http://stackoverflow.com/questions/14224172/equality-in-pandas-
        dataframes-column-order-matters
    """
    return assert_frame_equal(
        df1.sort(axis=1),
        df2.sort(axis=1),
        check_names=True, **kwargs)

test_df = pd.DataFrame(
    {'x': [1, 2, 3, 4], 'y': [4, 3, 2, 1]},
    columns=['x', 'y'])
test_series = pd.Series([1, 2, 3, 4])

test_dfsq = pd.DataFrame(
    {'x': [-2, -1, 0, 1, 2], 'xsq': [4, 1, 0, 1, 4]},
    columns=['x', 'xsq'])


class PlyWhereTest(unittest.TestCase):

    def test_no_conditions(self):
        assert_frame_equal(test_df.ply_where(), test_df)

    def test_single_condition(self):
        expected = pd.DataFrame(
            {'x': [3, 4], 'y': [2, 1]},
            index=[2, 3],
            columns=['x', 'y'])

        assert_frame_equal(test_df.ply_where(test_df.x > 2.5), expected)
        assert_frame_equal(test_df.ply_where(lambda df: df.x > 2.5), expected)
        assert_frame_equal(test_df.ply_where(X.x > 2.5), expected)

    def test_multiple_conditions(self):
        expected = pd.DataFrame(
            {'x': [2, 3], 'y': [3, 2]},
            index=[1, 2],
            columns=['x', 'y'])

        lo_df = test_df.x > 1.5
        hi_df = test_df.x < 3.5
        lo_func = lambda df: df.x > 1.5
        hi_func = lambda df: df.x < 3.5
        lo_sym = X.x > 1.5
        hi_sym = X.x < 3.5

        for lo in [lo_df, lo_func, lo_sym]:
            for hi in [hi_df, hi_func, hi_sym]:
                assert_frame_equal(test_df.ply_where(lo, hi), expected)


class PlyWhereForSeriesTest(unittest.TestCase):

    def test_no_conditions(self):
        assert_series_equal(test_series.ply_where(), test_series)

    def test_single_condition(self):
        expected = pd.Series([3, 4], index=[2, 3])

        assert_series_equal(test_series.ply_where(test_series > 2.5), expected)
        assert_series_equal(test_series.ply_where(lambda s: s > 2.5), expected)
        assert_series_equal(test_series.ply_where(X > 2.5), expected)

    def test_multiple_conditions(self):
        expected = pd.Series([2, 3], index=[1, 2])

        assert_series_equal(
            test_series.ply_where(test_series < 3.5, test_series > 1.5), expected)
        assert_series_equal(
            test_series.ply_where(test_series < 3.5, lambda s: s > 1.5), expected)
        assert_series_equal(
            test_series.ply_where(test_series < 3.5, X > 1.5), expected)
        assert_series_equal(
            test_series.ply_where(lambda s: s < 3.5, lambda s: s > 1.5), expected)
        assert_series_equal(
            test_series.ply_where(lambda s: s < 3.5, X > 1.5), expected)
        assert_series_equal(
            test_series.ply_where(X < 3.5, X > 1.5), expected)


class PlySelectTest(unittest.TestCase):

    def test_bad_arguments(self):
        # Nonexistent column, include or exclude
        with self.assertRaises(ValueError):
            test_df.ply_select('z')
        with self.assertRaises(ValueError):
            test_df.ply_select('-z')

        # Exclude without asterisk
        with self.assertRaises(ValueError):
            test_df.ply_select('-x')

        # Include with asterisk
        with self.assertRaises(ValueError):
            test_df.ply_select('*', 'x')

    def test_noops(self):
        assert_frame_equal(test_df.ply_select('*'), test_df)
        assert_frame_equal(test_df.ply_select('x', 'y'), test_df)
        assert_frame_equiv(test_df.ply_select(x=X.x, y=X.y), test_df)

    def test_reorder(self):
        reordered = test_df.ply_select('y', 'x')
        assert_frame_equiv(reordered, test_df[['y', 'x']])
        self.assertEqual(list(reordered.columns), ['y', 'x'])

    def test_subset_via_includes(self):
        assert_frame_equal(test_df.ply_select('x'), test_df[['x']])
        assert_frame_equal(test_df.ply_select('y'), test_df[['y']])

    def test_subset_via_excludes(self):
        assert_frame_equal(test_df.ply_select('*', '-y'), test_df[['x']])
        assert_frame_equal(test_df.ply_select('*', '-x'), test_df[['y']])

    def test_empty(self):
        assert_frame_equal(test_df.ply_select(), test_df[[]])
        assert_frame_equal(test_df.ply_select('*', '-x', '-y'), test_df[[]])

    def test_ways_of_providing_new_columns(self):
        # Value
        assert_frame_equal(
            test_df.ply_select(new=5),
            pd.DataFrame({'new': [5, 5, 5, 5]}))

        # Dataframe-like
        assert_frame_equal(
            test_df.ply_select(new=[5, 6, 7, 8]),
            pd.DataFrame({'new': [5, 6, 7, 8]}))

        # Function
        assert_frame_equal(
            test_df.ply_select(new=lambda df: df.x),
            pd.DataFrame({'new': [1, 2, 3, 4]}))

        # Symbolic expression
        assert_frame_equal(
            test_df.ply_select(new=X.x),
            pd.DataFrame({'new': [1, 2, 3, 4]}))

    def test_old_and_new_together(self):
        assert_frame_equal(
            test_df.ply_select('x', total=X.x + X.y),
            pd.DataFrame(
                {'x': [1, 2, 3, 4], 'total': [5, 5, 5, 5]},
                columns=['x', 'total']))

    def test_kwarg_overrides_asterisk(self):
        assert_frame_equal(
            test_df.ply_select('*', y=X.x),
            pd.DataFrame({'x': [1, 2, 3, 4], 'y': [1, 2, 3, 4]}))

    def test_kwarg_overrides_column_include(self):
        assert_frame_equal(
            test_df.ply_select('x', 'y', y=X.x),
            pd.DataFrame({'x': [1, 2, 3, 4], 'y': [1, 2, 3, 4]}))

    def test_new_index(self):
        assert_frame_equal(
            test_df.ply_select('x', index=X.y),
            pd.DataFrame(
                {'x': [1, 2, 3, 4]},
                index=pd.Index([4, 3, 2, 1], name='y')))


class PlySelectForGroupsTest(unittest.TestCase):

    def test_simple(self):
        grp = test_dfsq.groupby('xsq')
        assert_frame_equal(
            grp.ply_select(count=X.x.count()),
            pd.DataFrame(
                {'count': [1, 2, 2]},
                index=pd.Index([0, 1, 4], name='xsq')))
