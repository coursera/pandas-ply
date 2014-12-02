#!/bin/bash

ls test_*.py | xargs -n 1 python2.7
ls test_*.py | xargs -n 1 python3
