from setuptools import setup
from setuptools import find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='i3-resurrect',
    version='1.4.5',
    packages=['i3_resurrect'],
    author='Jonathan Haylett',
    author_email='jonathan@haylett.dev',
    url='https://github.com/JonnyHaystack/i3-resurrect',
    license='GNU GPL Version 3',
    python_requires='>=3.6',
    install_requires=[
        'Click',
        'i3ipc',
        'natsort',
        'psutil',
    ],
    entry_points={
        'console_scripts': ['i3-resurrect=i3_resurrect.main:main'],
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
