"""`ply.symbolic` is a simple system for building "symbolic expressions" to
provide as arguments to **pandas-ply**'s methods (in place of lambda
expressions)."""


class Expression:
    """`Expression` is the (abstract) base class for symbolic expressions.
    Symbolic expressions are encoded representations of Python expressions,
    kept on ice until you are ready to evaluate them. Operations on
    symbolic expressions (like `my_expr.some_attr` or `my_expr(some_arg)` or
    `my_expr + 7`) are automatically turned into symbolic representations
    thereof -- nothing is actually done until the special evaluation method
    `_eval` is called.
    """

    def _eval(self, context, **options):
        """Evaluate a symbolic expression.

        Args:
            context: The context object for evaluation. Currently, this is a
                dictionary mapping symbol names to values,
            `**options`: Options for evaluation. Currently, the only option is
                `log`, which results in some debug output during evaluation if
                it is set to `True`.

        Returns:
            anything
        """
        raise NotImplementedError

    def __repr__(self):
        raise NotImplementedError

    def __coerce__(self, other):
        return None

    def __getattr__(self, name):
        """Construct a symbolic representation of `getattr(self, name)`."""
        return GetAttr(self, name)

    def __call__(self, *args, **kwargs):
        """Construct a symbolic representation of `self(*args, **kwargs)`."""
        return Call(self, args=args, kwargs=kwargs)


# Here are the varieties of atomic / compound Expression.


class Symbol(Expression):
    """`Symbol(name)` is an atomic symbolic expression, labelled with an
    arbitrary `name`."""

    def __init__(self, name):
        self._name = name

    def _eval(self, context, **options):
        if options.get('log'):
            print 'Symbol._eval', repr(self)
        result = context[self._name]
        if options.get('log'):
            print 'Returning', repr(self), '=>', repr(result)
        return result

    def __repr__(self):
        return 'Symbol(%s)' % repr(self._name)


class GetAttr(Expression):
    """`GetAttr(obj, name)` is a symbolic expression representing the result of
    `getattr(obj, name)`. (`obj` and `name` can themselves be symbolic.)"""

    def __init__(self, obj, name):
        self._obj = obj
        self._name = name

    def _eval(self, context, **options):
        if options.get('log'):
            print 'GetAttr._eval', repr(self)
        evaled_obj = eval_if_symbolic(self._obj, context, **options)
        result = getattr(evaled_obj, self._name)
        if options.get('log'):
            print 'Returning', repr(self), '=>', repr(result)
        return result

    def __repr__(self):
        return 'getattr(%s, %s)' % (repr(self._obj), repr(self._name))


class Call(Expression):
    """`Call(func, args, kwargs)` is a symbolic expression representing the
    result of `func(*args, **kwargs)`. (`func`, each member of the `args`
    iterable, and each value in the `kwargs` dictionary can themselves be
    symbolic)."""

    def __init__(self, func, args=[], kwargs={}):
        self._func = func
        self._args = args
        self._kwargs = kwargs

    def _eval(self, context, **options):
        if options.get('log'):
            print 'Call._eval', repr(self)
        evaled_func = eval_if_symbolic(self._func, context, **options)
        evaled_args = [eval_if_symbolic(v, context, **options)
                       for v in self._args]
        evaled_kwargs = {k: eval_if_symbolic(v, context, **options)
                         for k, v in self._kwargs.iteritems()}
        result = evaled_func(*evaled_args, **evaled_kwargs)
        if options.get('log'):
            print 'Returning', repr(self), '=>', repr(result)
        return result

    def __repr__(self):
        return '{func}(*{args}, **{kwargs})'.format(
            func=repr(self._func),
            args=repr(self._args),
            kwargs=repr(self._kwargs))


def eval_if_symbolic(obj, context, **options):
    """Evaluate an object if it is a symbolic expression, or otherwise just
    returns it back.

    Args:
        obj: Either a symbolic expression, or anything else (in which case this
            is a noop).
        context: Passed as an argument to `obj._eval` if `obj` is symbolic.
        `**options`: Passed as arguments to `obj._eval` if `obj` is symbolic.

    Returns:
        anything

    Examples:
        >>> eval_if_symbolic(Symbol('x'), {'x': 10})
        10
        >>> eval_if_symbolic(7, {'x': 10})
        7
    """
    return obj._eval(context, **options) if hasattr(obj, '_eval') else obj


def to_callable(obj):
    """Turn an object into a callable.

    Args:
        obj: This can be

            * **a symbolic expression**, in which case the output callable
              evaluates the expression with symbols taking values from the
              callable's arguments (listed arguments named according to their
              numerical index, keyword arguments named according to their
              string keys),
            * **a callable**, in which case the output callable is just the
              input object, or
            * **anything else**, in which case the output callable is a
              constant function which always returns the input object.

    Returns:
        callable

    Examples:
        >>> to_callable(Symbol(0) + Symbol('x'))(3, x=4)
        7
        >>> to_callable(lambda x: x + 1)(10)
        11
        >>> to_callable(12)(3, x=4)
        12
    """
    if hasattr(obj, '_eval'):
        return lambda *args, **kwargs: obj._eval(dict(enumerate(args), **kwargs))
    elif callable(obj):
        return obj
    else:
        return lambda *args, **kwargs: obj


def sym_call(func, *args, **kwargs):
    """Construct a symbolic representation of `func(*args, **kwargs)`.

    This is necessary because `func(symbolic)` will not (ordinarily) know to
    construct a symbolic expression when it receives the symbolic
    expression `symbolic` as a parameter (if `func` is not itself symbolic).
    So instead, we write `sym_call(func, symbolic)`.

    Args:
        func: Function to call on evaluation (can be symbolic).
        `*args`: Arguments to provide to `func` on evaluation (can be symbolic).
        `**kwargs`: Keyword arguments to provide to `func` on evaluation (can be
            symbolic).

    Returns:
        `ply.symbolic.Expression`

    Example:
        >>> sym_call(math.sqrt, Symbol('x'))._eval({'x': 16})
        4
    """

    return Call(func, args=args, kwargs=kwargs)

X = Symbol(0)
"""A Symbol for "the first argument" (for convenience)."""
