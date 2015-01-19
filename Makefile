test:
	pip install -e .
	pip install "file://`pwd`#egg=sentry-auth-onelogin[tests]"
	py.test -x
