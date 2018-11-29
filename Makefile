test:
	python2 -m unittest
	python3 -m unittest

run:
	python ./samples/sample_device.py

build:
	python3 setup.py sdist bdist_wheel --universal
	
upload:
	twine upload dist/*

clean:
	rm -rf .trash
	mkdir -p .trash/scpidev/pyc
	-mv -f scpidev/__pycache__ .trash/scpidev/;  true
	-mv -f scpidev/tests/__pycache__ .trash/scpidev/tests/; true
	-find scpidev/. -name "*.pyc" -exec mv {} .trash/scpidev/pyc/ \;; true
	-mv -f build .trash; true
	-mv -f dist .trash; true
	-mv -f scpidev.egg-info .trash; true

cleaner: clean
	rm -rf .trash
