all:
	python __main__.py


t: test
test:
	python -m pytest test_*.py

