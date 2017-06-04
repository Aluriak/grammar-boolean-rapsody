gbr:
	python gbr.py

dat:
	python interf_data.py


t: test
test:
	python -m pytest test_*.py

