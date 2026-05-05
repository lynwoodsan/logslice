"""Setup configuration for logslice."""

from setuptools import setup, find_packages

setup(
    name="logslice",
    version="0.1.0",
    description="Stream and filter large log files by time range, level, or regex pattern.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="logslice contributors",
    python_requires=">=3.8",
    packages=find_packages(exclude=["tests*"]),
    entry_points={
        "console_scripts": [
            "logslice=logslice.cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Topic :: System :: Logging",
        "Topic :: Utilities",
    ],
    install_requires=[],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov",
        ]
    },
)
