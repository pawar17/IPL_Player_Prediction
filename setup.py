from setuptools import setup, find_packages

setup(
    name="ipl_player_prediction",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "pandas",
        "scikit-learn",
        "joblib",
        "requests",
        "beautifulsoup4",
        "python-dotenv",
        "schedule",
        "fake-useragent"
    ],
    python_requires=">=3.8",
) 