import os
import unittest

from factorioccn.__main__ import main


class TestRunExamples(unittest.TestCase):
    def test_run_examples(self):
        for file in os.listdir('./examples'):
            if file.endswith('.fccn'):
                with self.subTest(file):
                    main('./examples/' + file)
