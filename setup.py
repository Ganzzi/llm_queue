"""Setup script for llm-queue package."""

from setuptools import setup

# Read version from __version__.py
version = {}
with open("src/llm_queue/__version__.py") as f:
    exec(f.read(), version)

# Read long description from README
with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="llm-queue",
    version=version["__version__"],
    author=version["__author__"],
    author_email=version["__email__"],
    description="A high-performance Python package for managing LLM API calls with intelligent rate limiting",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Ganzzi/llm-queue",
    project_urls={
        "Bug Tracker": "https://github.com/Ganzzi/llm-queue/issues",
        "Documentation": "https://llm-queue.readthedocs.io",
        "Source Code": "https://github.com/Ganzzi/llm-queue",
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP",
        "Typing :: Typed",
    ],
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=[
        "pydantic>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "pytest-benchmark>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "pre-commit>=3.0.0",
        ],
        "docs": [
            "mkdocs>=1.4.0",
            "mkdocs-material>=9.0.0",
            "mkdocstrings[python]>=0.20.0",
        ],
    },
)
