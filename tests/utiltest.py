#!/usr/bin/env python

import sys
import unittest

sys.path.append('.')
sys.path.append('..')

import goldbug

class FreqAnalTest(unittest.TestCase):
    def test_freqanal(self):
        self.assertEqual(goldbug.util.frequency_analysis("mississipi", 1),
                         {'m': 1. / 10, 'i': 4. / 10,
                          's': 4. / 10, 'p': 1. / 10})
        self.assertEqual(goldbug.util.frequency_analysis("mississipi", 2),
                         {'mi': 1. / 9, 'is': 2. / 9, 'ss': 2. / 9,
                          'si': 2. / 9, 'ip': 1. / 9, 'pi': 1. / 9})
        self.assertEqual(goldbug.util.frequency_analysis("mississipi", 3),
                         {'mis': 1. / 8, 'iss': 2. / 8, 'ssi': 2. / 8,
                          'sis': 1. / 8, 'sip': 1. / 8, 'ipi': 1. / 8})
        self.assertEqual(goldbug.util.frequency_analysis("mississipi", 9),
                         {'mississip': 1. / 2, 'ississipi': 1. / 2})
        self.assertEqual(goldbug.util.frequency_analysis("mississipi", 10),
                         {'mississipi': 1})
        self.assertEqual(goldbug.util.frequency_analysis("mississipi", 11),
                         {})


if __name__ == '__main__':
    unittest.main()