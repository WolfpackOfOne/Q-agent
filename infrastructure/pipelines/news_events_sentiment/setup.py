from setuptools import setup, find_packages

setup(
    name='news_events_sentiment_lean',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    install_requires=[
        'requests>=2.34.2',
        'pandas>=2.2.0',
    ],
)
