.PHONY: test validate

test:
	python3 -m unittest discover -s tests

# the clean context must pass; the leaky one must fail
validate: test
	python3 dockerignorelint.py examples/good
	! python3 dockerignorelint.py examples/leaky > /dev/null
