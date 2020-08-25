# simple Makefile for some common tasks
.PHONY: clean test dist release pypi tagv docs

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
	git tag -s \
		-m `python -c 'import gabbi; print gabbi.__version__'` \
		`python -c 'import gabbi; print gabbi.__version__'`
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
