.PHONY: run
run:
	poetry run req2flatpak

.PHONY: lint
lint:
	poetry run pre-commit run --all-files

.PHONY: test
test:
	poetry run python3 -m unittest

.PHONY: docs
docs:
	poetry run sphinx-build -v -b html docs/source docs/build/html
