# -*- coding: utf-8 -*-

import argparse
import sys

if sys.platform == "win32":
    from colorama import init as colorama_init
    colorama_init(autoreset=True)

ap = argparse.ArgumentParser()
