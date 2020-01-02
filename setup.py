import setuptools

from dcluster import __version__


with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="dcluster",  # Replace with your own username
    version=__version__,
    author="Giacomo Mc Evoy Valenzano",
    author_email="giacomo.valenzano@atos.net",
    description="Create and manage Docker clusters, optionally run Ansible on the cluster.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com",
    # packages=['dcluster', 'dcluster.tests'],
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=2.7',
    test_suite="dcluster/tests"
)
