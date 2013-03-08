#!/usr/bin/env python
# coding=utf8

"""
This module implements a number of classical cryptographic algorithms. All of
these should considered broken; they are provided for educational and historical
purposes, not security.
"""

import itertools
import math
import string

try:
    from itertools import izip
except ImportError:
    izip = zip


from . import util


class Cipher(object):
    """
    Base class for all ciphers. Don't instantiate this.
    """
    def encrypt(self, text):
        raise NotImplementedError

    def decrypt(self, text):
        raise NotImplementedError

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.key)


# Substitution ciphers

class MonoalphabeticSubstitutionCipher(Cipher):
    """
    Abstract base class for ciphers that use monoalphabetic substitutions.
    """
    def encrypt(self, text):
        """
        Encrypts the given text. Plaintext case will be preserved in the
        ciphertext, to the extent that this makes sense.
        """
        return ''.join((type(text).lower, type(text).upper)[c.isupper()]\
                       (self.encrypt_mapping.get(c.lower(), c)) for c in text)

    def decrypt(self, text):
        """
        Decrypts the given text. Ciphertext case will be preserved in the
        plaintext, to the extent that this makes sense.
        """
        return ''.join((type(text).lower, type(text).upper)[c.isupper()]\
                       (self.decrypt_mapping.get(c.lower(), c)) for c in text)


class Affine(MonoalphabeticSubstitutionCipher):
    """
    The affine cipher is a monoalphabetic substitution cipher that maps each
    letter of the alphabet to another one through a simple mathematical
    function. Its key consists of two integers, a and b, the first of which
    must be prime relative to the length of the alphabet.

    To encrypt a letter, it is transformed into a number (A becomes 0, B
    becomes 1, etc.), which is multiplied by a and incremented by b modulo the
    length of the alphabet. The resulting number is turned back into a letter.

    The decryption step is the same in reverse: the number is decremented by b
    and multiplied by a's multiplicative inverse modulo the length of the
    alphabet.
    """
    def __init__(self, key, alphabet='abcdefghijklmnopqrstuvwxyz'):
        """
        key is a tuple of integers, the first of which must be prime relative
        to the length of the alphabet.
        """
        self.alphabet = alphabet.lower()
        self.key = key
        a, b = key

        # Decryption mapping.
        # Doing this one first so we don't have to waste time if a doesn't
        # have a multiplicative inverse modulo len(alphabet).
        mmi = util.mmi(a, len(alphabet))
        self.decrypt_mapping = dict(
            (c, alphabet[mmi * (alphabet.index(c) - b) % len(alphabet)])
            for c in alphabet
        )

        # Encryption mapping.
        self.encrypt_mapping = dict(
            (c, alphabet[(a * alphabet.index(c) + b) % len(alphabet)])
            for c in alphabet
        )

    def __repr__(self):
        return '%s(%r, alphabet=%r)' % (self.__class__.__name__,
                                        self.key, self.alphabet)

class Atbash(MonoalphabeticSubstitutionCipher):
    """
    Atbash is a keyless substitution cipher, originally for the Hebrew
    alphabet. It consists of substituting the first letter of the alphabet for
    the last, the second for the penultimate, and so on; hence the name (אתבש).
    It is a reciprocal cipher, meaning two successive applications will yield
    the original plaintext.

    This implementation works on the 26-letter Latin alphabet by default.
    """
    def __init__(self, alphabet="abcdefghijklmnopqrstuvwxyz"):
        """
        alphabet is the alphabet to use, in the right order.
        """
        self.alphabet = alphabet.lower()
        self.encrypt_mapping = dict(zip(self.alphabet, self.alphabet[::-1]))
        self.decrypt_mapping = self.encrypt_mapping

    def __repr__(self):
        return '%s(alphabet=%r)' % (self.__class__.__name__, self.alphabet)

class Caesar(MonoalphabeticSubstitutionCipher):
    """
    The Caesar cipher, also known as the shift cipher or Caesar shift, is a
    monoalphabetic substitution cipher in which each letter of the alphabet is
    replaced by a letter some fixed number of positions down the alphabet.
    This number is the key.

    It is named after Julius Caesar, who supposedly used it for his personal
    correspondence.
    """
    def __init__(self, key):
        """
        key should be an integer, practically between 0 and 26.
        """
        self.key = int(key) % 26
        shifted = [chr(ord('a') + (ord(c) - ord('a') + key) % 26) for c in
                   string.ascii_lowercase]
        self.encrypt_mapping = dict(zip(string.ascii_lowercase, shifted))
        self.decrypt_mapping = dict(zip(shifted, string.ascii_lowercase))

class FourSquare(Cipher):
    """
    The four-square cipher is a polygraphic substitution cipher by Felix
    Delastelle.
    It takes as its key two Polybius squares, and operates on plaintext
    characters within the domain of a third. These squares, all of which are
    the same size, are arranged thusly:

        ALPHABET    KEY1
        KEY2        ALPHABET

    By way of a example, consider two keys Polybius('example') and
    Polybius('keyword'), and a basic alphabet Polybius(''). Arranged, they
    look like this:

        a b c d e  e x a m p
        f g h i k  l b c d f
        l m n o p  g h i k n
        q r s t u  o q r s t
        v w x y z  u v w y z

        k e y w o  a b c d e
        r d a b c  f g h i k
        f g h i l  l m n o p
        m n p q s  q r s t u
        t u v x z  v w x y z

    Encryption happens by taking plaintext character in pairs, and locating
    the first one in the top left square and the second in the bottom right
    one. The ciphertext characters are then the characters on the other two
    corners of the rectangle they form.
    """
    def __init__(self, keys, alphabet=util.Polybius(''), padding='x'):
        """
        keys must be a sequence of two Polybius squares.
        alphabet must be a Polybius square.
        padding must be a character in alphabet.
        All squares must be the same size.
        """
        if len(keys) != 2:
            raise ValueError('Need exactly two keys.')

        if len(keys[0]) != len(keys[1]) or len(keys[0]) != len(alphabet):
            raise ValueError('All squares must be the same size!')

        if keys[0].dimensions != 2 or keys[1].dimensions != 2 or \
           alphabet.dimensions != 2:
            raise ValueError('All squares must be squares!')

        if len(padding) != 1:
            raise ValueError('Padding character must be character!')

        if padding not in alphabet:
            raise ValueError('Padding character must exist in alphabet!')

        self.keys = keys
        self.alphabet = alphabet
        self.padding = padding

    def encrypt(self, text):
        """
        Transforms plaintext into ciphertext.
        """
        if len(text) % 2 == 1:
            text += self.padding
        text = (c for c in text)
        cipher = []
        for a, b in zip(text, text):
            x1, y1 = self.alphabet[a]
            x2, y2 = self.alphabet[b]
            cipher.append(self.keys[0][x1, y2])
            cipher.append(self.keys[1][x2, y1])
        return ''.join(cipher)

    def decrypt(self, text):
        """
        Transforms ciphertext into plaintext.
        """
        text = (c for c in text)
        plain = []
        for a, b in zip(text, text):
            x1, y1 = self.keys[0][a]
            x2, y2 = self.keys[1][b]
            plain.append(self.alphabet[x1, y2])
            plain.append(self.alphabet[x2, y1])
        return ''.join(plain)

    def __repr__(self):
        return '%s(%r, %r)' % (self.__class__.__name__,
                               self.keys, self.alphabet)

class Hill(Cipher):
    """
    The Hill cipher is a polygraphic substitution cipher based on matrix
    operations, designed by Lester S. Hill in 1929.

    Each letter of the key, plaintext, and ciphertext is represented as a
    number in some way; for instance, a=0, b=1, etc. The key is written as
    a square matrix. For instance, if our key is "ddcf":

        3 3
        2 5

    The plaintext is broken up into chunks of a length equal to the key
    matrix's side, and written as a column matrix. The key matrix and the
    plaintext matrix are then multiplied modulo the length of the alphabet to
    yield the ciphertext. For instance, if our message is "help":

        3 3 * 7 = 7 (H)
        2 5   4   8 (I)

        3 3 * 11 = 0 (A)
        2 5   15   19 (T)

    Our ciphertext is then "hiat".

    Decryption is the same process, only using the inverse of the key matrix
    modulo the length of the alphabet. This inverse doesn't exist for every
    matrix, so choose your key with care.
    """
    def __init__(self, key, alphabet=string.ascii_lowercase):
        """
        key must be an instance of goldbug.util.Matrix, invertible modulo the
        alphabet length, or a string to be translated into one.
        alphabet must not have any repeated characters.
        """
        if len(set(alphabet)) != len(alphabet):
            raise ValueError('Invalid alphabet!')
        self.alphabet = alphabet
        self.modulus = len(alphabet)

        if not isinstance(key, util.Matrix):
            w = int(round(len(key) ** .5))
            if w * w != len(key):
                raise ValueError("Key can't be transformed into square matrix!")
            key = [self.alphabet.index(c) for c in key]
            key = util.Matrix([key[i:i + w] for i in range(0, len(key), w)])
        self.key = key % self.modulus
        self.invkey = pow(key, -1, self.modulus)

    def encrypt(self, text):
        """
        Transforms plaintext into ciphertext.
        """
        cipher = []
        for i in range(0, len(text), self.key.rows):
            chunk = util.Matrix(list(zip(self.alphabet.index(c)
                                         for c in text[i:i + self.key.rows])))
            m = self.key * chunk % self.modulus
            cipher.extend([self.alphabet[c] for c in m.col(0)])
        return ''.join(cipher)

    def decrypt(self, text):
        """
        Transforms ciphertext into plaintext.
        """
        plain = []
        for i in range(0, len(text), self.invkey.rows):
            chunk = util.Matrix(list(zip(self.alphabet.index(c)
                                         for c in text[i:i + self.invkey.rows])))
            m = self.invkey * chunk % self.modulus
            plain.extend([self.alphabet[c] for c in m.col(0)])
        return ''.join(plain)

    def __repr__(self):
        if self.alphabet == string.ascii_lowercase:
            return '%s(%r)' % (self.__class__.__name__, self.key)
        else:
            return '%s(%r, alphabet=%r)' % (self.__class__.__name__,
                                            self.key, self.alphabet)

class KamaSutra(MonoalphabeticSubstitutionCipher):
    """
    The Kama Sutra cipher is an early substitution cipher described in the
    Kama Sutra. It is also known as the Vatsyayana cipher, after its
    purported author.

    Its key is a permutation of the alphabet. This permutation is written
    in two rows, and each plaintext character is replaced with the
    corresponding character in the other row.
    For example, if our key is 'vqajflymsbckuhzdxtenorpwig':

        v q a j f l y m s b c k u
        h z d x t e n o r p w i g

    v is replaced with h, e is replace with l, etc.
    Decryption is the exact same process.
    """
    def __init__(self, key):
        """
        key is an ordered permutation of the alphabet.
        """
        self.key = key
        self.encrypt_mapping = {}
        for i in range(len(key)):
            self.encrypt_mapping[key[i]] = key[(i + len(key) // 2) % len(key)]
        self.decrypt_mapping = self.encrypt_mapping

class Keyword(MonoalphabeticSubstitutionCipher):
    """
    The keyword cipher is a monoalphabetic substitution cipher using a keyword
    as the key. The alphabet is appended to the key, and duplicate letters are
    removed. The result is then aligned with the plaintext alphabet to obtain
    the substitution mapping.

    For example, with the key "SECRET":

    Plaintext:  A B C D E F G H I J K L M N O P Q R S T U V W X Y Z
    Ciphertext: S E C R T A B D F G H I J K L M N O P Q U V W X Y Z
    """
    def __init__(self, key):
        self.key = key.lower()
        m = []
        for c in key + string.ascii_lowercase:
            if c not in m:
                m.append(c)
        self.encrypt_mapping = dict(zip(string.ascii_lowercase, m))
        self.decrypt_mapping = dict(zip(m, string.ascii_lowercase))

class Playfair(MonoalphabeticSubstitutionCipher):
    """
    The Playfair cipher is a digraph substitution cipher invented by Charles
    Wheatstone in 1854 and popularised by Lord Playfair.
    """
    def __init__(self, key, breaker='x', padding='z', omitted={'j': 'i'}):
        """
        key is a short string.
        breaker is the letter with which duplicate pairs are broken up.
        omitted is a mapping. ({'q': ''} is common).
        """
        # Ensure omitted is proper and lowercase.
        if not isinstance(omitted, dict):
            raise ValueError('omitted must be a dict!')
        self.omitted = dict((k.lower(), v.lower()) for k, v in omitted.items())

        # Adjust the alphabet to take omitted into account.
        self.alphabet = ''.join(c for c in string.ascii_lowercase
                                if c not in self.omitted)
        if len(self.alphabet) != 25 or \
           any(len(c) > 1 or c not in self.alphabet
               for c in self.omitted.values()):
            raise ValueError('Malformed omitted!')

        # Ensure the breaker is alright.
        self.breaker = breaker
        if len(breaker) != 1 or breaker not in self.alphabet:
            raise ValueError('Breaker %s not in alphabet!' % breaker)

        # Ensure the padding is alright.
        self.padding = padding
        if len(padding) != 1 or padding not in self.alphabet:
            raise ValueError('Padding %s not in alphabet!' % padding)

        # Clean the key.
        self.key = key
        key = ''.join(c for c in key.lower() if c in self.alphabet)

        # Construct the Polybius square.
        self.polybius = util.Polybius(key, self.alphabet)

    # Playfair is a monoalphabetic substitution cipher, but because it
    # works with bigrams rather than individual letters, we can't reuse
    # MonoalphabeticSubstitutionCipher's methods.

    def encrypt(self, text):
        """
        Turn provided plaintext into ciphertext.
        """
        return ''.join(self.__polyb(b) for b in self.__plain_pairs(text))

    def decrypt(self, text):
        """
        Turn provided ciphertext into plaintext.
        """
        return ''.join(self.__polyb(b, True) for b in self.__cipher_pairs(text))

    def __plain_pairs(self, text):
        """
        Turns plaintext into proper digraphs (tuples) for encryption.
        """
        # Convert mappings.
        text = ''.join(self.omitted.get(c, c) for c in text)

        # Get rid of repeated breaker characters.
        while self.breaker + self.breaker in text:
            text = text.replace(self.breaker + self.breaker, self.breaker)

        # Pad.
        text += self.padding

        plain = (c for c in text.lower() if c in self.alphabet)
        for a, b in izip(plain, plain):
            if a == b:
                yield a, self.breaker
                c = next(plain)
                while c == b:
                    yield b, self.breaker
                    c = next(plain)
                yield b, c
            else:
                yield a, b

    def __cipher_pairs(self, text):
        """
        Turns ciphertext into proper digraphs (tuples) for decryption.
        Will raise ValueError is ciphertext is bogus.
        """
        if len(text) % 2 != 0:
            raise ValueError('Ciphertext of uneven length!')
        cipher = (self.omitted.get(c, c) for c in text)
        for a, b in zip(cipher, cipher):
            if a == b:
                raise ValueError('Invalid ciphertext!')
            yield a, b

    def __polyb(self, digraph, decrypt=False):
        """
        Translates a digraph through the Polybius square.
        """
        r1, c1 = self.polybius[digraph[0]]
        r2, c2 = self.polybius[digraph[1]]

        if r1 != r2 and c1 != c2:
            return self.polybius[(r1, c2)] + self.polybius[(r2, c1)]
        elif r1 == r2:
            if decrypt:
                c1 = (c1 - 1) % 5
                c2 = (c2 - 1) % 5
            else:
                c1 = (c1 + 1) % 5
                c2 = (c2 + 1) % 5
        elif c1 == c2:
            if decrypt:
                r1 = (r1 - 1) % 5
                r2 = (r2 - 1) % 5
            else:
                r1 = (r1 + 1) % 5
                r2 = (r2 + 1) % 5
        return self.polybius[(r1, c1)] + self.polybius[(r2, c2)]

    def __repr__(self):
        return '%s(%r, breaker=%r, padding=%r, omitted=%r)' % \
               (self.__class__.__name__, self.key, self.breaker, self.padding,
                self.omitted)

class Rot13(Caesar):
    """
    ROT13 is a special case of the Caesar cipher. In effect, it is the Caesar
    cipher with the key set to 13. It is a reciprocal cipher, meaning two
    successive applications will yield the original text.

    It became particularly popular on Usenet, where it was often used to
    obscure spoilers and punchlines to jokes.
    """
    def __init__(self):
        super(Rot13, self).__init__(13)

    def __repr__(self):
        return '%s()' % self.__class__.__name__

class Simple(MonoalphabeticSubstitutionCipher):
    """
    The simplest substitution cipher just maps characters to other characters.
    """
    def __init__(self, key):
        """
        key: a dict mapping characters to other characters.
        """
        self.key = key
        self.encrypt_mapping = self.key
        self.decrypt_mapping = dict((b, a) for (a, b) in self.key.items())

class Homophonic(Simple):
    """
    The homophonic substitution cipher can match plaintext characters to any
    of a number of ciphertext characters.

    This class is just an alias for goldbug.cipher.Simple; pass it a
    goldbug.util.RandomDict instead of a normal dictionary to make it behave
    as a homophonic cipher.
    """

class TwoSquare(Cipher):
    """
    The two-square cipher, also called double Playfair, uses two Polybius
    squares compared to four-square's four. It arranges them horizontally or
    vertically, and transforms plaintext pairs into ciphertext pairs in the
    same way as four-square, with the exception that if they're on the same
    column (vertical arrangement) or row (horizontal arrangement), they are
    preserved.
    """
    def __init__(self, keys, horizontal=False):
        """
        keys: two Polybius squares sharing an alphabet.
        The squares are arranged vertically unless horizontal is True.
        """
        if set(keys[0].contents) != set(keys[1].contents):
            raise ValueError('Polybius squares must share an alphabet!')
        self.keys = keys
        self.horizontal = bool(horizontal)

    def encrypt(self, text):
        """
        Transforms plaintext into ciphertext.
        """
        lastchar = text[-1] if len(text) % 2 == 1 else ''
        text = (c for c in text)
        cipher = []
        for a, b in zip(text, text):
            r1, c1 = self.keys[0][a]
            r2, c2 = self.keys[1][b]

            if self.horizontal:
                if r1 == r2:
                    cipher.append(a)
                    cipher.append(b)
                else:
                    cipher.append(self.keys[0][r2, c1])
                    cipher.append(self.keys[1][r1, c2])
            else:
                if c1 == c2:
                    cipher.append(a)
                    cipher.append(b)
                else:
                    cipher.append(self.keys[0][r1, c2])
                    cipher.append(self.keys[1][r2, c1])
        cipher.append(lastchar)
        return ''.join(cipher)

    def decrypt(self, text):
        """
        Transforms ciphertext into plaintext.
        """
        return self.encrypt(text)

    def __repr__(self):
        return '%s(%r, horizontal=%r)' % (self.__class__.__name__,
                                          self.keys, self.horizontal)

class Vigenere(Cipher):
    """
    The Vigenere cipher is a simple polyalphabetic substitution cipher first
    described by Giovan Battista Bellaso in 1553, and later misattributed to
    Blaise de Vigenere. Though it is easy to understand and implement, it often
    appears difficult to break, earning it its nickname as "le chiffre
    indechiffrable".

    Its key is a word or short phrase, which is repeated for the length of the
    plaintext. If our key is lemon and our plaintext is attackatdawn, this
    looks like this:

        lemonlemonle
        attackatdawn

    The corresponding key and plaintext characters are then looked up in a
    tabula recta, yielding a ciphertext character.
    """
    def __init__(self, key, alphabet=string.ascii_lowercase):
        """
        key is a short string, all of whose characters must appear in the
        alphabet.
        """
        if not all(c in alphabet for c in key):
            raise ValueError('Invalid key!')
        self.key = key
        self.alphabet = alphabet

    def encrypt(self, text):
        """
        Transform plaintext into ciphertext.
        """
        tabula = util.TabulaRecta(self.alphabet)
        return ''.join(tabula[co] for co in zip(text, self.__keystream()))

    def decrypt(self, text):
        """
        Transform ciphertext into plaintext.
        """
        tabula = util.TabulaRecta(self.alphabet, reverse=True)
        return ''.join(tabula[co] for co in zip(text, self.__keystream()))

    def __keystream(self):
        while True:
            for c in self.key:
                yield c

    def __repr__(self):
        if self.alphabet == string.ascii_lowercase:
            return '%s(%r)' % (self.__class__.__name__, self.key)
        else:
            return '%s(%r, alphabet=%r)' % (self.__class__.__name__,
                                            self.key, self.alphabet)

class Autokey(Vigenere):
    """
    The autokey or autoclave cipher is a variation on the Vigenere cipher in
    which, rather than repeating the key for the length of the plaintext, the
    plaintext is appended to the key.
    """
    def encrypt(self, text):
        """
        Transform plaintext into ciphertext.
        """
        tabula = util.TabulaRecta(self.alphabet)
        return ''.join(tabula[co] for co in zip(text, self.key + text))

    def decrypt(self, text):
        """
        Transform ciphertext into plaintext.
        """
        tabula = util.TabulaRecta(self.alphabet, reverse=True)
        key = list(self.key)
        plain = []
        for i in range(len(text)):
            c = tabula[text[i], key[i]]
            plain.append(c)
            key.append(c)
        return ''.join(plain)

# Transposition ciphers

class Column(Cipher):
    """
    The columnar transposition cipher is a fairly straightforward transposition
    cipher, which permutes plaintext in two steps.

    First, the plaintext is padded until its length is a multiple of the key
    length and placed into columns below the key, as follows:

        C I P H E R
        t h i s i s
        a n e x a m
        p l e x x x

    In this example, the plaintext is "thisisanexample", the key is "CIPHER",
    and the padding character is "x".

    In the second step, the columns are moved so that the key's characters are
    in alphabetical order:

        C E H I P R
        t i s h i s
        a a x n e m
        p x x l e x

    Then the key row is removed, and the columns are catenated to form the
    ciphertext; in this case, "tapiaxsxxhnlieesmx".

    By itself, the columnar transposition cipher is fairly easy to break, but
    it continued to be used as part of more complex encryption schemes until
    some time into the 1950s.
    """
    def __init__(self, key, pad='x'):
        """
        key is a short string with no repeated characters.
        pad is a single character.
        """
        if len(key) < 1:
            raise ValueError('Invalid key!')
        for c in key:
            if key.count(c) > 1:
                raise ValueError('Each key character must be unique!')
        self.key = key

        if len(pad) != 1:
            raise ValueError('pad must be one character!')
        self.pad = pad

    def encrypt(self, text):
        """
        Encrypts the provided plaintext.
        """
        # Pad the plaintext until it's rectangular.
        if len(text) % len(self.key):
            text += self.pad * (len(self.key) - len(text) % len(self.key))

        # Assemble the columns.
        columns = [text[i::len(self.key)] for i in range(len(self.key))]

        # Index them by ciphertext character and sort alphabetically.
        columns = dict((k, v) for k, v in zip(self.key, columns))
        return ''.join(columns[k] for k in sorted(self.key))

    def decrypt(self, text):
        """
        Decrypts the provided ciphertext.
        """
        if len(text) % len(self.key) != 0:
            raise ValueError('Not a valid ciphertext.')
        rows = len(text) // len(self.key)

        # Break the ciphertext up in columns.
        columns = [text[i * rows:(i + 1) * rows] for i in range(len(self.key))]

        # Index the columns by their key character.
        columns = dict((k, c) for k, c in zip(sorted(self.key), columns))

        # Restore their original order.
        columns = [columns[c] for c in self.key]

        # Just read off the plaintext.
        return ''.join(''.join(row) for row in zip(*columns)).rstrip(self.pad)

    def __repr__(self):
        return '%s(%r, pad=%r)' % (self.__class__.__name__, self.key, self.pad)

class RailFence(Cipher):
    """
    Rail Fence cipher.
    """
    def __init__(self, key):
        self.key = int(key)
        if key < 1:
            raise ValueError('Key should be strictly positive!')

    def encrypt(self, text):
        """
        Transforms plaintext into ciphertext.
        """
        if self.key == 1:
            # Degenerate case.
            return text

        rails = [[] for _ in range(self.key)]
        indices = itertools.cycle(list(range(self.key - 1)) +
                                  list(range(self.key - 1, 0, -1)))
        for c in text:
            rails[next(indices)].append(c)
        return ''.join(sum(rails, []))

    def decrypt(self, text):
        """
        Transforms ciphertext into plaintext.
        """
        if self.key == 1:
            # Degenerate case.
            return text

        # We're going to divide the ciphertext back up into rows. This is
        # slightly tricky.
        # Consider that each ciphertext has a period of a certain length
        # depending on the key (equal to (key - 1) * 2):
        #
        # <---------> <---------> <---------> <--
        # x . . . . . x . . . . . x . . . . . x .
        # . d . . . a . d . . . a . d . . . r . d
        # . . d . a . . . d . a . . . d . r . . .
        # . . . x . . . . . x . . . . . x . . . .
        #
        # Each row other than the top and bottom has a number of characters on
        # the descending limb (d on the figure) equal to the number of periods
        # for a text of a length equal to the total ciphertext length minus the
        # row number (if top is 0), and a number of characters on the ascending
        # limb (a on the figure) equal to the number of periods for a text of a
        # length equal to the total ciphertext length minus the row number,
        # minus the first skip, which is the distance from d to a.
        # That first skip is equal to the key minus the row number minus 1,
        # times 2.
        # Therefore we can calculate the number of characters on each row and
        # use that information to divide our ciphertext.
        #
        # The top and bottom row are special in that their ascending and
        # descending characters coincide, but that makes them easier to
        # calculate; the top row is just the number of periods, and the bottom
        # is everything that's left over.

        rows = []

        # Top row is special.
        rowend = int(math.ceil(self.__periods(len(text))))
        rows.append(text[:rowend])

        rowstart = rowend
        for i in range(1, self.key - 1):
            periods = self.__periods(len(text) - i)
            rowend = int(
                rowstart +
                math.ceil(self.__periods(len(text) - i)) +  # descending
                math.ceil(self.__periods(len(text) - i -
                          (self.key - i - 1) * 2))          # ascending
            )
            rows.append(text[rowstart:rowend])
            rowstart = rowend

        # Bottom row is special too.
        rows.append(text[rowstart:])

        # Now just go up and down the rows.
        gens = [(c for c in row) for row in rows]
        indices = itertools.cycle(list(range(self.key - 1)) +
                                  list(range(self.key - 1, 0, -1)))
        return ''.join(next(gens[next(indices)]) for _ in range(len(text)))

    def __periods(self, length):
        """
        Calculates the number of periods present in a text of the given length.

        For instance, for a key of 3 and a length of 10, this is 2.5:

        <--1--> <--2--> <--
        x . . . x . . . x .
        . x . x . x . x . x
        . . x . . . x . . .

        """
        return float(length) / ((self.key - 1) * 2)


# Other ciphers

class Bifid(Cipher):
    """
    The bifid cipher, invented around 1901 by Felix Delastelle, combines
    fractionated substitution with transmutation by way of a Polybius square,
    which is the cipher key.

    To demonstrate, let's assume we're using the following Polybius square:

        B G W K Z
        Q P N D S
        I O A X E
        F C L U M
        T H Y V R

    To encrypt a message, the plaintext characters' coordinates in the Polybius
    square are written vertically in a row, and the rows are then joined.
    Suppose our plaintext is "FLEEATONCE":

        F L E E A T O N C E
        3 3 2 2 2 4 2 1 3 2     <- X coordinate
        0 2 4 4 2 0 1 2 1 4     <- Y coordinate

        => 3 3 2 2 2 4 2 1 3 2 0 2 4 4 2 0 1 2 1 4

    These numbers are then taken pairwise as the coordinates of our ciphertext
    characters:

        (3, 3) -> U
        (2, 2) -> A
        etc.

        => UAEOLWRINS

    Decryption is the same thing in reverse.

    Longer messages are usually broken up into smaller components. The length
    of these components is the period of the cipher.
    """
    def __init__(self, key, period=0):
        """
        key should be a string or a Polybius square.
        period should be an integer; non-positive not to use one.
        """
        if not isinstance(key, util.Polybius):
            key = util.Polybius('', key)
        if key.dimensions != 2:
            raise ValueError('Polybius instance must be square!')
        self.polybius = key
        self.period = int(period)

    def encrypt(self, text):
        """
        Transforms plaintext into ciphertext.
        """
        if self.period > 0:
            blocks = (self.__encrypt_block(text[i * self.period
                                               :(i + 1) * self.period])
                           for i in range(len(text) // self.period + 1))
            return ''.join(blocks)
        else:
            return self.__encrypt_block(text)

    def decrypt(self, text):
        """
        Transforms ciphertext into plaintext.
        """
        if self.period > 0:
            blocks = (self.__decrypt_block(text[i * self.period
                                               :(i + 1) * self.period])
                           for i in range(len(text) // self.period + 1))
            return ''.join(blocks)
        else:
            return self.__decrypt_block(text)

    def __encrypt_block(self, text):
        # Look up the coordinates of each plaintext character.
        coords = [self.polybius[c] for c in text.lower()]

        # Write them in columns and read the rows.
        coords = sum(tuple(zip(*coords)), ())

        # Look up the characters for each new pair of coordinates.
        return ''.join(self.polybius[coords[i:i + self.polybius.dimensions]]
                       for i in range(0, len(coords), self.polybius.dimensions))

    def __decrypt_block(self, text):
        # Look up the coordinates of each ciphertext character.
        coords = sum([self.polybius[c] for c in text], ())

        # Divide into equal rows and join them up for the original coordinates.
        rowlen = len(coords) // self.polybius.dimensions
        rows = [coords[i:i + rowlen] for i in range(0, len(coords), rowlen)]
        coords = zip(*rows)

        # Look up the plaintext characters.
        return ''.join(self.polybius[tuple(co)] for co in coords)

    def __repr__(self):
        if self.period > 0:
            return '%s(%r, %r)' % (self.__class__.__name__,
                                   self.polybius.contents, self.period)
        else:
            return '%s(%r)' % (self.__class__.__name__, self.polybius.contents)

class Trifid(Bifid):
    """
    The trifid cipher is another cipher by Felix Delastelle. It extends the
    concept of his bifid cipher into the third dimension; where the bifid
    cipher uses a Polybius square as the key, the trifid cipher uses a stack
    of n n x n Polybius squares (where n is canonically 3) as a Polybius
    cube.

    Other than dealing with three coordinates instead of two, the trifid
    cipher works in essentially the same way as the bifid cipher.
    """
    def __init__(self, key, period=0):
        """
        key is a string of a length with an integral cube root (canonically 27)
        or a Polybius cube.
        period is an integer; if not positive, texts aren't divided into
        blocks.
        """
        if not isinstance(key, util.Polybius):
            key = util.Polybius('', key, 3)
        if key.dimensions != 3:
            raise ValueError('Key must be a Polybius cube!')
        self.polybius = key
        self.period = int(period)
