#!/usr/bin/env python
import argparse
import sys

import django
from django.conf import settings
from django.test.utils import get_runner


def run_tests(test_labels=None):
    test_labels = test_labels or ['tests']
    settings.configure(INSTALLED_APPS=['tests'])
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(test_labels)
    sys.exit(failures)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('test_labels', nargs='*', default=['tests'])
    args = parser.parse_args()
    run_tests(test_labels=args.test_labels)
