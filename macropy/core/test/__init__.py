from macropy.test import test_suite

import unittest
import quotes
import unparse
import walkers
import macros
Tests = test_suite(cases = [
    quotes,
    unparse,
    walkers,
    macros
])