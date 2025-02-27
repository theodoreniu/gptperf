from setuptools import setup, find_packages

setup(
    name="llmperf",
    version="0.0.1",
    description="A CLI tool for LLM performance testing",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Theodore",
    author_email="theodore.niu@gmail.com",
    url="https://github.com/theodoreniu/llmperf",
    packages=find_packages(),
    install_requires=[
        "click",
    ],
    entry_points={
        "console_scripts": [
            "llmperf = cli.main:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
