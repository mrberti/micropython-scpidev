test:
	python2 -m unittest
	python3 -m unittest

build:
	python3 setup.py sdist bdist_wheel --universal
	
upload:
	twine upload dist/*

clean:
#	rm -rf .trash
	mkdir -p .trash/scpidev/pyc
	-mv -f scpidev/__pycache__ .trash/scpidev/ 2>/dev/null; true
	-mv -f scpidev/tests/__pycache__ .trash/scpidev/tests/ 2>/dev/null; true
	-mv -f scpidev/*/*.pyc .trash/scpidev/pyc/ 2>/dev/null; true
	-mv -f build .trash 2>/dev/null; true
	-mv -f dist .trash 2>/dev/null; true
	-mv -f scpidev.egg-info .trash 2>/dev/null; true
