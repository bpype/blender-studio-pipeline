# How to run tests

Tests require [Blender as Python Module](https://pypi.org/project/bpy/) which in turn currently requires Python 3.11 and not higher.

1. **Install Python 3.11**
    Windows: Download & install from https://www.python.org/downloads/release/python-3117/
    Other OS: Figure it out.
1. **Creating Python virtual environment in the repo's root**
    `cd path/to/blender-studio-tools/scripts-blender/addons`
    Windows: `py -3.11 -m venv venv`
    Linux: `python3.11 -m venv .venv`
1. **Activate Python 3.11 venv**
    Windows: `.\venv\Scripts\activate`
    Linux: `. .venv/bin/activate`
1. **Install dependencies**
    `pip install -r requirements-dev.txt`
1. **Run (verbose) tests**
    `pytest -v`
1. **Run tests with coverage visualization**
    `pip install coverage pytest-cov`
    `pytest -v --durations=0 --cov=./asset_pipeline --cov-report=html --cov-branch`
    Replace "asset_pipeline" with folder name of the add-on you want coverage of.
    Durations of test executions will be printed in the terminal.
    Coverage stats can be seen by opening `htmlcov/index.html` file in a web browser.

# What if a test fails
- Figure out which test is failing and why: In the output of PyTest, under the `= FAILURES =` section, you'll find a line number, possibly with an assert or some other error. Find that line of code in the `tests` directory and take a look around.
- It can be useful to understand how PyTest's [fixtures](https://docs.pytest.org/en/stable/explanation/fixtures.html) work; If you see a function parameter like `context_curves`, it's probably a fixture that loads `tests/blends/curves.blend`.
- If a failure happens inside a .blend file, it's probably a good idea to open that blend file, try to understand what the test code is doing and what it is expecting, and then repeat those steps manually and observe how the output becomes different from what the test is expecting.
    - For example, `tests/test_pose_consistency.py` will re-generate a bunch of posed rigs, and assert that their bone transforms are the same as before. If that test fails, you can simply open the relevant .blend file, go to the frame number defined by the `obj_frame_map` dict in the test's code, and re-generate the rig while looking carefully, using your eyeballs, which bones move to different transforms than they were in before, and why.
- If the difference in output is an expected improvement, then the test is considered outdated - You can update the test (modify the .blend file or the test code), and consider this change a backwards compatibility break for the next CloudRig version. **Backwards compatibility breaks are fine, as long as they are warranted, kept track of, and mitigated when reasonably possible.**
- If the output is is unexpectedly different, it should give you a strong clue about which part of your code is wrong.

# Contribute
You can see a list of desired tests [here](https://projects.blender.org/Mets/CloudRig/issues/242). To be able to help implement them, you just need to be able to run the tests locally using the instructions above, then learn a bit about the [pytest](https://docs.pytest.org/en/stable/) module.
From there, since tests live in this repository, the contribution process is the same [fork+branch+pull request workflow](https://developer.blender.org/docs/handbook/contributing/pull_requests/) as it is for Blender itself.
