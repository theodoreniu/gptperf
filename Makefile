init:
	pip install twine build setuptools
	pip install -r requirements.txt

install:
	pip install -e .

publish:
	python3 -m build --sdist --wheel --outdir dist/ .
	twine upload dist/*