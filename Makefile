test:
	python2 -m unittest
	python3 -m unittest

build:
	python3 setup.py sdist bdist_wheel --universal
	
upload:
	twine upload dist/*

clean:
	rm -rf .trash
	mkdir -p .trash/pyc
	-mv scpidev/__pycache__ .trash/scpidev/ 2>/dev/null; true
	-mv scpidev/*/*.pyc .trash/pyc/ 2>/dev/null; true
	-mv build .trash 2>/dev/null; true
	-mv dist .trash 2>/dev/null; true
	-mv scpidev.egg-info .trash 2>/dev/null; true
