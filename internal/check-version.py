#!/usr/bin/env python
import os
import subprocess
import semver
import sys
import re
from pathlib import Path
from git import Repo

version_re = r"^v[0-9].[0-9].[0-9]"

with open(Path("../", "VERSION"), "r") as f:
    version = f.readline().strip("\n")

if not re.search(version_re, version):
    print("VERSION must match %s", version_re)
    sys.exit(1)

repo = Repo(Path("../"))
latest_tag = repo.tags[-1].name.strip("v")

if semver.compare(version.strip("v"), latest_tag) != 1:
    print("VERSION must be iterated")
    sys.exit(1)
