import sys
if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest
import mock

from ply.symbolic import Call
from ply.symbolic import GetAttr
from ply.symbolic import Symbol
from ply.symbolic import eval_if_symbolic
from ply.symbolic import sym_call
from ply.symbolic import to_callable


class ExpressionTest(unittest.TestCase):

    # These test whether operations on symbolic expressions correctly construct
    # compound symbolic expressions:

    def test_getattr(self):
        expr = Symbol('some_symbol').some_attr
        self.assertEqual(
            repr(expr),
            "getattr(Symbol('some_symbol'), 'some_attr')")

    def test_call(self):
        expr = Symbol('some_symbol')('arg1', 'arg2', kwarg_name='kwarg value')
        self.assertEqual(
            repr(expr),
            "Symbol('some_symbol')(*('arg1', 'arg2'), " +
            "**{'kwarg_name': 'kwarg value'})")

    def test_ops(self):
        expr = Symbol('some_symbol') + 1
        self.assertEqual(
            repr(expr),
            "getattr(Symbol('some_symbol'), '__add__')(*(1,), **{})")

        expr = 1 + Symbol('some_symbol')
        self.assertEqual(
            repr(expr),
            "getattr(Symbol('some_symbol'), '__radd__')(*(1,), **{})")

        expr = Symbol('some_symbol')['key']
        self.assertEqual(
            repr(expr),
            "getattr(Symbol('some_symbol'), '__getitem__')(*('key',), **{})")


class SymbolTest(unittest.TestCase):

    def test_eval(self):
        self.assertEqual(
            Symbol('some_symbol')._eval({'some_symbol': 'value'}),
            'value')
        self.assertEqual(
            Symbol('some_symbol')._eval(
                {'some_symbol': 'value', 'other_symbol': 'irrelevant'}),
            'value')
        with self.assertRaises(KeyError):
            Symbol('some_symbol')._eval({'other_symbol': 'irrelevant'}),

    def test_repr(self):
        self.assertEqual(repr(Symbol('some_symbol')), "Symbol('some_symbol')")


class GetAttrTest(unittest.TestCase):

    def test_eval_with_nonsymbolic_object(self):
        some_obj = mock.Mock()
        del some_obj._eval
        # Ensure constructing the expression does not access `.some_attr`.
        del some_obj.some_attr

        with self.assertRaises(AttributeError):
            some_obj.some_attr
        expr = GetAttr(some_obj, 'some_attr')

        some_obj.some_attr = 'attribute value'

        self.assertEqual(expr._eval({}), 'attribute value')

    def test_eval_with_symbolic_object(self):
        some_obj = mock.Mock()
        del some_obj._eval
        some_obj.some_attr = 'attribute value'

        expr = GetAttr(Symbol('some_symbol'), 'some_attr')

        self.assertEqual(
            expr._eval({'some_symbol': some_obj}),
            'attribute value')

    def test_repr(self):
        self.assertEqual(
            repr(GetAttr('object', 'attrname')),
            "getattr('object', 'attrname')")


class CallTest(unittest.TestCase):

    def test_eval_with_nonsymbolic_func(self):
        func = mock.Mock(return_value='return value')
        del func._eval  # So it doesn't pretend to be symbolic

        expr = Call(func, ('arg1', 'arg2'), {'kwarg_name': 'kwarg value'})

        # Ensure constructing the expression does not call the function
        self.assertFalse(func.called)

        result = expr._eval({})

        func.assert_called_once_with('arg1', 'arg2', kwarg_name='kwarg value')
        self.assertEqual(result, 'return value')

    def test_eval_with_symbolic_func(self):
        func = mock.Mock(return_value='return value')
        del func._eval  # So it doesn't pretend to be symbolic

        expr = Call(
            Symbol('some_symbol'),
            ('arg1', 'arg2'),
            {'kwarg_name': 'kwarg value'})

        result = expr._eval({'some_symbol': func})

        func.assert_called_once_with('arg1', 'arg2', kwarg_name='kwarg value')
        self.assertEqual(result, 'return value')

    def test_eval_with_symbolic_arg(self):
        func = mock.Mock(return_value='return value')
        del func._eval  # So it doesn't pretend to be symbolic

        expr = Call(
            func,
            (Symbol('some_symbol'), 'arg2'),
            {'kwarg_name': 'kwarg value'})

        result = expr._eval({'some_symbol': 'arg1'})

        func.assert_called_once_with('arg1', 'arg2', kwarg_name='kwarg value')
        self.assertEqual(result, 'return value')

    def test_eval_with_symbol_kwarg(self):
        func = mock.Mock(return_value='return value')
        del func._eval  # So it doesn't pretend to be symbolic

        expr = Call(
            func,
            ('arg1', 'arg2'),
            {'kwarg_name': Symbol('some_symbol')})

        result = expr._eval({'some_symbol': 'kwarg value'})

        func.assert_called_once_with('arg1', 'arg2', kwarg_name='kwarg value')
        self.assertEqual(result, 'return value')

    def test_repr(self):
        # One arg
        self.assertEqual(
            repr(Call('func', ('arg1',), {'kwarg_name': 'kwarg value'})),
            "'func'(*('arg1',), **{'kwarg_name': 'kwarg value'})")

        # Two args
        self.assertEqual(
            repr(Call(
                'func',
                ('arg1', 'arg2'),
                {'kwarg_name': 'kwarg value'})),
            "'func'(*('arg1', 'arg2'), **{'kwarg_name': 'kwarg value'})")


class FunctionsTest(unittest.TestCase):

    def test_eval_if_symbolic(self):
        self.assertEqual(
            eval_if_symbolic(
                'nonsymbolic',
                {'some_symbol': 'symbol_value'}),
            'nonsymbolic')
        self.assertEqual(
            eval_if_symbolic(
                Symbol('some_symbol'),
                {'some_symbol': 'symbol_value'}),
            'symbol_value')

    def test_to_callable_from_nonsymbolic_noncallable(self):
        test_callable = to_callable('nonsymbolic')
        self.assertEqual(
            test_callable('arg1', 'arg2', kwarg_name='kwarg value'),
            'nonsymbolic')

    def test_to_callable_from_nonsymbolic_callable(self):
        func = mock.Mock(return_value='return value')
        del func._eval  # So it doesn't pretend to be symbolic

        test_callable = to_callable(func)

        # Ensure running to_callable does not call the function
        self.assertFalse(func.called)

        result = test_callable('arg1', 'arg2', kwarg_name='kwarg value')

        func.assert_called_once_with('arg1', 'arg2', kwarg_name='kwarg value')
        self.assertEqual(result, 'return value')

    def test_to_callable_from_symbolic(self):
        mock_expr = mock.Mock()
        mock_expr._eval.return_value = 'eval return value'

        test_callable = to_callable(mock_expr)

        # Ensure running to_callable does not evaluate the expression
        self.assertFalse(mock_expr._eval.called)

        result = test_callable('arg1', 'arg2', kwarg_name='kwarg value')

        mock_expr._eval.assert_called_once_with(
            {0: 'arg1', 1: 'arg2', 'kwarg_name': 'kwarg value'})
        self.assertEqual(result, 'eval return value')

    def test_sym_call(self):
        expr = sym_call(
            'func', Symbol('some_symbol'), 'arg1', 'arg2',
            kwarg_name='kwarg value')
        self.assertEqual(
            repr(expr),
            "'func'(*(Symbol('some_symbol'), 'arg1', 'arg2'), " +
            "**{'kwarg_name': 'kwarg value'})")


class IntegrationTest(unittest.TestCase):

    def test_pythagoras(self):
        from math import sqrt

        X = Symbol('X')
        Y = Symbol('Y')

        expr = sym_call(sqrt, X ** 2 + Y ** 2)
        func = to_callable(expr)

        self.assertEqual(func(X=3, Y=4), 5)
