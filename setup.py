from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='i3-resurrect',
    version='1.0.2',
    author='Jonathan Haylett',
    author_email='jonathan@haylett.dev',
    py_modules=['i3_resurrect'],
    url='https://github.com/JonnyHaystack/i3-resurrect',
    license='GNU GPL Version 3',
    install_requires=[
        'Click',
        'wmctrl-python3',
        'i3ipc',
        'psutil',
    ],
    entry_points={
        'console_scripts': ['i3-resurrect=i3_resurrect:main'],
    },
    description=('A simple but flexible solution to saving and restoring i3 '
                 'workspace layouts'),
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: POSIX :: Linux",
    ],
)
