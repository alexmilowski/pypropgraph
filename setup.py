import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

import re
vdir = __file__[0:__file__.rfind('/')]+'/' if __file__.rfind('/')>=0 else ''
VERSIONFILE = vdir+'propgraph/__init__.py'
with open(VERSIONFILE, 'rt') as vfile:
   verstrline = vfile.read()
   VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
   mo = re.search(VSRE, verstrline, re.M)
   if mo:
      version_info = mo.group(1)
   else:
      raise RuntimeError("Unable to find version string in %s." % (VERSIONFILE,))

setuptools.setup(
    name="pypropgraph",
    version=version_info,
    author='Alex Miłowski',
    author_email='alex@milowski.com',
    description='A property graphs library for python',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/alexmilowski/pypropgraph',
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    keywords='cypher property graph',
    python_requires='>=3.6',
    install_requires=['lark-parser','redis','redisgraph','pyyaml']
)
