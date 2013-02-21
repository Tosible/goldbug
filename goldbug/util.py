#!/usr/bin/env python 

"""
Utilities for studying and breaking classical ciphers.
"""

import collections

def frequency_analysis(text, ngram=1):
    """
    Generates an n-gram frequency table from a source text.
    """
    freqs, total = collections.defaultdict(int), 0
    for i in range(len(text) - ngram + 1):
        freqs[text[i:i + ngram]] += 1
        total += 1
    for gram in freqs:
        freqs[gram] /= float(total)
    return dict(freqs)

def chi2(text, freqs):
    """
    Performs Pearson's chi-squared test on a potential plaintext with respect
    to a given frequency table. Lower numbers are better.
    freqs should be a table from goldbug.freq.*; for instance, to perform the
    test with respect to English monograms, use goldbug.freq.english.monogram.
    """
    acc = 0
    for c in freqs:
        e_i = freqs[c] * len(text) / len(c) # Expected incidence
        c_i = text.count(c)                 # Observed incidence
        if e_i == 0.0 and c_i == 0:
            continue
        elif e_i == 0.0:
            acc += float('inf')
        else:
            acc += (c_i - e_i)**2 / e_i
    return acc
