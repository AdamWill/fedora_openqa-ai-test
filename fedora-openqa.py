#!/usr/bin/python3

import os
import sys

# add src subdirectory directory to module import path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), 'src'))

from fedora_openqa.cli import main

if __name__ == '__main__':
    main()
