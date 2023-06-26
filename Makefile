# simple Makefile for some common tasks
.PHONY: clean test dist release pypi tagv docs

gabbi-version := $(shell python -c 'import gabbi; print(gabbi.__version__)')

clean:
	find . -name "*.pyc" |xargs rm || true
	rm -r dist || true
	rm -r build || true
	rm -rf .tox || true
	rm -r .testrepository || true
	rm -r cover .coverage || true
	rm -r .eggs || true
	rm -r gabbi.egg-info || true

tagv:
	git tag -s -m ${gabbi-version} ${gabbi-version}
	git push origin main --tags

cleanagain:
	find . -name "*.pyc" |xargs rm || true
	rm -r dist || true
	rm -r build || true
	rm -r .tox || true
	rm -r .testrepository || true
	rm -r cover .coverage || true
	rm -r .eggs || true
	rm -r gabbi.egg-info || true

docs:
	cd docs ; $(MAKE) html

test:
	tox --skip-missing-interpreters

dist: test
	python3 setup.py sdist bdist_wheel

release: clean test cleanagain tagv pypi

pypi:
	python3 setup.py sdist bdist_wheel
	twine upload -s dist/*

docker:
	docker build --build-arg GABBI_VERSION=${gabbi-version} -t gabbi:${gabbi-version} .
