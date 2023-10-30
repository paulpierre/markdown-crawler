from setuptools import setup, find_packages

setup(
    name="markdown-crawler",
    packages=find_packages(exclude=['markdown']),
    include_package_data=True,
)