#!/bin/bash
VERSION=`python -c "import propgraph; print('.'.join(map(str,propgraph.__version__)))"`
AUTHOR=`python -c "import propgraph; print(propgraph.__author__)"`
EMAIL=`python -c "import propgraph; print(propgraph.__author_email__)"`
DESCRIPTION=`python -c "import propgraph; print(propgraph.__doc__)"`
REQUIRES=`python -c "list(map(print,['\t'+line.strip() for line in open('requirements.txt', 'r').readlines()]))"`
LONG_DESC=`python -c "list(map(print,['\t'+line.strip() for line in open('README.md', 'r').readlines()]))"`
cat <<EOF > setup.cfg
[metadata]
name = pypropgraph
version = ${VERSION}
author = ${AUTHOR}
author_email = ${EMAIL}
description = ${DESCRIPTION}
license = MIT License
url = https://github.com/alexmilowski/pypropgraph
keywords=
   cypher
   property
   graph
long_description=
${LONG_DESC}
long_description_content_type = text/markdown

[options]
packages =
   propgraph
include_package_data = True
install_requires =
${REQUIRES}

[options.package_data]
* = *.json, *.yaml, *.flow

[options.extras_require]
redis = 
   redis
falkordb =
   FalkorDB
EOF
