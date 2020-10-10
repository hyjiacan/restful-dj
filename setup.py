import setuptools

VERSION = '2.0.0-beta2'

with open("README.md", "r", encoding="utf8") as fh:
    long_description = fh.read()

setuptools.setup(
    name='restful-dj',
    version=VERSION,
    packages=setuptools.find_packages(),
    include_package_data=True,
    url='http://github.com/hyjiacan/restful-dj',
    license='MIT',
    author='hyjiacan',
    author_email='hyjiacan@163.com',
    description='restful(and auto route) support for Django2/3',
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.5',
)
