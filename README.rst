**pandas-ply**: functional data manipulation for pandas
=======================================================

**pandas-ply** is a thin layer which makes it easier to manipulate data with `pandas <http://pandas.pydata.org/>`_. In particular, it provides elegant, functional, chainable syntax in cases where **pandas** would require mutation, saved intermediate values, or other awkward constructions. In this way, it aims to move **pandas** closer to the "grammar of data manipulation" provided by the `dplyr <http://cran.r-project.org/web/packages/dplyr/index.html>`_ package for R.

For example, take the **dplyr** code below:

.. code:: r

  flights %>%
    group_by(year, month, day) %>%
    summarise(
      arr = mean(arr_delay, na.rm = TRUE),
      dep = mean(dep_delay, na.rm = TRUE)
    ) %>%
    filter(arr > 30 & dep > 30)

The most common way to express this in **pandas** is probably:

.. code:: python

  grouped_flights = flights.groupby(['year', 'month', 'day'])
  output = pd.DataFrame()
  output['arr'] = grouped_flights.arr_delay.mean()
  output['dep'] = grouped_flights.arr_delay.mean()
  filtered_output = output[(output.arr > 30) & (output.dep > 30)]

**pandas-ply** lets you instead write:

.. code:: python

  (flights
    .groupby(['year', 'month', 'day'])
    .ply_select(
      arr = X.arr_delay.mean(),
      dep = X.dep_delay.mean())
    .ply_where(X.arr > 30, X.dep > 30))

In our opinion, this **pandas-ply** code is cleaner, more expressive, more readable, more concise, and less error-prone than the original **pandas** code.

Explanatory notes on the **pandas-ply** code sample above:

* **pandas-ply**'s methods (like ``ply_select`` and ``ply_where`` above) are attached directly to **pandas** objects and can be used immediately, without any wrapping or redirection. They start with a ``ply_`` prefix to distinguish them from built-in **pandas** methods.
* **pandas-ply**'s methods are named for (and modelled after) SQL's operators. (But keep in mind that these operators will not always appear in the same order as they do in a SQL statement: ``SELECT a FROM b WHERE c GROUP BY d`` probably maps to ``b.ply_where(c).groupby(d).ply_select(a)``.)
* **pandas-ply** includes a simple system for building "symbolic expressions" to provide as arguments to its methods. ``X`` above is an instance of ``ply.symbolic.Symbol``. Operations on this symbol produce larger compound symbolic expressions. When ``pandas-ply`` receives a symbolic expression as an argument, it converts it into a function. So, for instance, ``X.arr > 30`` in the above code could have instead been provided as ``lambda x: x.arr > 30``. Use of symbolic expressions allows the ``lambda x:`` to be left off, resulting in less cluttered code.

Warning
-------

**pandas-ply** is new, and in an experimental stage of its development. The API is not yet stable. Expect the unexpected.

(Pull requests are welcome. Feel free to contact us at pandas-ply@coursera.org.)

Using **pandas-ply**
--------------------

Install **pandas-ply** with:

::

  $ pip install pandas-ply


Typical use of **pandas-ply** starts with:

.. code:: python

  import pandas as pd
  from ply import install_ply, X, sym_call

  install_ply(pd)

After calling ``install_ply``, all **pandas** objects have **pandas-ply**'s methods attached.

API reference
-------------

Full API reference is available at `<http://pythonhosted.org/pandas-ply/>`_.

Possible TODOs
--------------

* Extend ``pandas``' native ``groupby`` to support symbolic expressions?
* Extend ``pandas``' native ``apply`` to support symbolic expressions?
* Add ``.ply_call`` to ``pandas`` objects to extend chainability?
* Version of ``ply_select`` which supports later computed columns relying on earlier computed columns?
* Version of ``ply_select`` which supports careful column ordering?
* Better handling of indices?

License
-------

Copyright 2014 Coursera Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
