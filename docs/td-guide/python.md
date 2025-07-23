# Python Setup
## Install Python
The Blender Studio Pipeline requires `Python 3.11` or greater to be installed on your system.

## Windows
1. Navigate to https://www.python.org/downloads/windows/ to download & install the latest version of Python 3.11+
2. On the first page of the installer, ensure the option labelled “Add Python to PATH” is enabled
3. After installation, open a command prompt/terminal window, enter `python --version`, if installation was successful the python version you installed should be printed in your command prompt/terminal window.

## Mac
1. Navigate to https://www.python.org/downloads/mac/ to download & install the latest version of Python 3.11+
2. Run the install wizard to install python
3. In the `Applications/Python 3.11` directory double-click `Update Shell Profile.command`
4. In the `Applications/Python 3.11` directory double-click `Install Certificates.command`
5. After installation, open a command prompt/terminal window, enter `python --version`, if installation was successful the python version you installed should be printed in your command prompt/terminal window.

## Linux
Python is pre-installed on many distributions. Here is how to explicitly install python on some common distributions. 

**Gentoo**
```bash
emerge --ask dev-lang/python:3
```

**Ubuntu/Debian**
```bash
apt-get install python3
apt install python-is-python3 
```

**Arch Linux**
```bash
pacman -S python
```

After installation, open a command prompt/terminal window, enter `python --version`, if installation was successful the python version you installed should be printed in your command prompt/terminal window.

::: info Note 
This documentation expects `python --version` to return a python that is 3.8+. Please ensure you have setup your environment correctly or modify the example commands to your environment's needs (e.g. use `python3 --version` instead of `python --version`). To learn more see this [article](https://stackoverflow.com/questions/64801225/python-or-python3-what-is-the-difference).
:::

## Install Dependencies  

The Blender Studio Pipeline depends on scripts that require packages from the PIP package manager. The following is a guide to installing the required packages, on your system's python. To avoid module clutter consider setting up a virtual environment see the [official Python Documentation](https://docs.python.org/3/library/venv.html) for details.

1. Ensure PIP is installed `python -m ensurepip --upgrade`
2. Install required 'requests' package `python -m pip install requests`