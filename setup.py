import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="wordpress_orm",
    version="1.0.0",
    author="Demitri Muna",
    author_email="demitri@github.com",
    description="A object-oriented Python wrapper for the WordPress API.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/demitri/wordpress_orm",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
