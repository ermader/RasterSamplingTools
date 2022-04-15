from setuptools import setup, find_packages

with open("README.md", "r") as file:
    long_description = file.read()

setup(
    name="RasterSamplingTools",
    version="1.0.6",
    packages=find_packages(),
    package_data={
        "": ["FontDatabase.json"],
    },

    python_requires=">=3.9",
    install_requires=[
        "FontDocTools >= 1.2.1",
        "UnicodeData >= 0.2",
        "PathLib >= 0.2",
        "TestArguments >= 0.3",
        "numpy >= 1.21.2",
        "matplotlib >= 3.4.3",
        "openpyxl >= 3.0.9",
        "scipy >= 1.7.1",
        "statsmodels >= 0.13.2",
    ],

    entry_points={
        "console_scripts": [
            "rastersamplingtest = RasterSamplingTools.RasterSamplingTest:main",
            "rastersamplingtool = RasterSamplingTools.RasterSamplingTool:main",
            "summarize = RasterSamplingTools.Summarize:main",
        ]
    },

    author="Eric Mader",
    author_email="eric.mader@gmx.us",
    description="Tools for analyzing fonts.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ermader/RasterSamplingTool/",
    license_files=["LICENSE.md"],

    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: MacOS :: MacOS X",
        "Programming Language :: Python :: 3.9",
        "Topic :: Text Processing :: Fonts",
    ]
)
