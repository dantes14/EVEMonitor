#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = [line.strip() for line in f.readlines() if not line.startswith("#") and line.strip()]

setup(
    name="evemonitor",
    version="0.1.0",
    author="dantes14",
    author_email="[你的邮箱]",
    description="EVE游戏监控工具",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dantes14/EVEMonitor",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Games/Entertainment",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "evemonitor=src.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "src": ["config/*.yaml", "assets/*"],
    },
) 