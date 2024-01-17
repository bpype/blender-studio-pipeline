# Python Setup
## Install Python
The Blender Studio Pipeline requires `Python 3.11` or greater to be installed on your system.

## Windows & Mac
1. Navigate to https://www.python.org/downloads/windows/ to download & install the latest version of Python
2. On the first page of the installer, ensure the option labelled “Add Python to PATH” is enabled
3. After installation, open a command prompt/terminal window, enter `python --version`, if installation was successful the python version you installed should be printed in your command prompt/terminal window.

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
packman -S python
```

After installation, open a command prompt/terminal window, enter `python --version`, if installation was successful the python version you installed should be printed in your command prompt/terminal window.

## Install Dependencies  

The Blender Studio Pipeline depends on scripts that require packages from the PIP package manager. The following is a guide to installing the required packages, on your system's python. To avoid module clutter consider setting up a virtual environment see the [official Python Documentation](https://docs.python.org/3/library/venv.html) for details.

1. Ensure PIP is installed `python -m ensurepip --upgrade`
2. Install required 'requests' package `python -m pip install requests`