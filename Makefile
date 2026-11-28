.PHONY: run
run:
	poetry run req2flatpak

.PHONY: lint
lint:
	poetry run pre-commit run --all-files

.PHONY: test
test:
	poetry run python3 -m unittest -v

# Like "test", but without tests_flatpak/, which needs flatpak and an installed GNOME runtime.
.PHONY: test-no-flatpak
test-no-flatpak:
	poetry run python3 -m unittest discover -v -s tests -t .

.PHONY: docs
docs:
	poetry run sphinx-build -v -b html docs/source docs/build/html
