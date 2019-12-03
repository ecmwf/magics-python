# (C) Copyright 1996-2019 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation nor
# does it submit to any jurisdiction.
"""
A unittest script which dynamically adds tests based on the contents of the 'gallery'
directory.
"""
import os
import glob
import unittest
import subprocess


class MagicsSanityTest(unittest.TestCase):
    """
    A class with dynamically-generated test methods.
    """

    pass


def cleanup_backup(backup_name, original_name):
    """
    Move a backed-up file back to its original name.
    """
    print("Replacing {} with {}".format(original_name, backup_name))
    if os.path.isfile(backup_name):
        os.rename(backup_name, original_name)


def cleanup_output(output_name):
    """
    Delete a file created by running a test script.
    """
    print("Removing {}".format(output_name))
    os.remove(output_name)


def generate_test_method(test_name):
    """
    Generate a test method based on a given test name.

    The test is simply to run a test script 'test_name.py' and check that an output file with the
    name 'test_name.png' is generated.
    """

    def run_test(self):
        # backup any existing files with our expected output_name
        output_name = "{}.png".format(test_name)
        backup_name = output_name + ".backup"
        if os.path.isfile(output_name):
            os.rename(output_name, backup_name)
            self.addCleanup(cleanup_backup, backup_name, output_name)

        # run the test
        ret = subprocess.call("python {}.py".format(test_name), shell=True)
        self.assertEqual(ret, 0)

        output_exists = os.path.isfile(output_name)
        if output_exists:
            self.addCleanup(cleanup_output, output_name)

        ps_output_name = "{}.ps".format(test_name)
        if os.path.isfile(ps_output_name):
            # some tests may also generate postscript files which need to be deleted
            self.addCleanup(cleanup_output, ps_output_name)

        self.assertTrue(output_exists)

    return run_test


# This code needs to be outside of `if __name__ == '__main__'` so the test methods are generated
# at import time so that pytest can find them
test_dir = os.getenv("MAGICS_PYTHON_TESTS")
if not test_dir:
    test_dir = "./gallery"
os.chdir(test_dir)

for file_name in glob.glob("*.py"):
    test_name = os.path.splitext(file_name)[0]
    print("Adding test: {}".format(test_name))
    method_name = "test_{}".format(test_name)
    setattr(MagicsSanityTest, method_name, generate_test_method(test_name))

if __name__ == "__main__":
    unittest.main()
