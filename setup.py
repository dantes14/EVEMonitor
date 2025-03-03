#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = [line.strip() for line in f.readlines() if not line.startswith("#") and line.strip()]

setup(
    name="EVEMonitor",
    version="1.0.0",
    author="EVE监视器开发团队",
    author_email="your_email@example.com",
    description="EVE：无烬星河模拟器监控工具",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/EVEMonitor",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Games/Entertainment",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "evemonitor=EVEMONITOR.src.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "EVEMONITOR": ["config/*.yaml", "assets/*"],
    },
) 