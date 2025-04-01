from setuptools import setup, find_packages

setup(
    name="ipl_player_prediction",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'pandas',
        'numpy',
        'scikit-learn',
        'xgboost',
        'requests',
        'joblib'
    ]
) 