# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import os
import pathlib
import pytest
import shutil
import subprocess
import tempfile
import json
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent


def test_skip_ci():
    skip_ci_script = REPO_ROOT / "tests" / "scripts" / "git_skip_ci.sh"

    class TempGit:
        def __init__(self, cwd):
            self.cwd = cwd

        def run(self, *args):
            proc = subprocess.run(["git"] + list(args), cwd=self.cwd)
            if proc.returncode != 0:
                raise RuntimeError(f"git command failed: '{args}'")

    def test(commands, should_skip, why):
        with tempfile.TemporaryDirectory() as dir:
            git = TempGit(dir)
            # Jenkins git is too old and doesn't have 'git init --initial-branch'
            git.run("init")
            git.run("checkout", "-b", "main")
            git.run("commit", "--allow-empty", "--message", "base commit")
            for command in commands:
                git.run(*command)
            proc = subprocess.run([str(skip_ci_script)], cwd=dir)
            expected = 1 if should_skip else 0
            assert proc.returncode == expected, why

    test(
        commands=[],
        should_skip=False,
        why="ci should not be skipped",
    )

    test(
        commands=[
            ["commit", "--allow-empty", "--message", "[skip ci] commit 1"],
        ],
        should_skip=False,
        why="ci should not be skipped on main",
    )

    test(
        commands=[
            ["checkout", "-b", "some_new_branch"],
            ["commit", "--allow-empty", "--message", "[skip ci] commit 1"],
        ],
        should_skip=True,
        why="ci should be skipped on a branch with [skip ci] in the last commit",
    )

    test(
        commands=[
            ["checkout", "-b", "some_new_branch"],
            ["commit", "--allow-empty", "--message", "[skip ci] commit 1"],
            ["commit", "--allow-empty", "--message", "commit 2"],
        ],
        should_skip=False,
        why="ci should not be skipped on a branch without [skip ci] in the last commit",
    )

    test(
        commands=[
            ["checkout", "-b", "some_new_branch"],
            ["commit", "--allow-empty", "--message", "[skip ci] commit 1"],
            ["commit", "--allow-empty", "--message", "commit 2"],
        ],
        should_skip=False,
        why="ci should not be skipped on a branch without [skip ci] in the last commit",
    )

    test(
        commands=[
            ["checkout", "-b", "some_new_branch"],
            ["commit", "--allow-empty", "--message", "commit 1"],
            ["commit", "--allow-empty", "--message", "commit 2"],
            ["commit", "--allow-empty", "--message", "commit 3"],
            ["commit", "--allow-empty", "--message", "commit 4"],
        ],
        should_skip=False,
        why="ci should not be skipped on a branch without [skip ci] in the last commit",
    )


if __name__ == "__main__":
    sys.exit(pytest.main([__file__] + sys.argv[1:]))