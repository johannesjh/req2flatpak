# This makefile demonstrates how to run req2flatpak using flatpak,
# to list installed packages and find out more about the flatpak runtime.

.PHONY: installed-packages
installed-packages:
	# lists packages that are installed in a given flatpak runtime
	flatpak-builder --force-clean --repo=_repo _build installed-packages.json
	flatpak-builder --run _build installed-packages.json installed-packages

.PHONY: platform-info
platform-info:
	# lists platform info about a given flatpak runtime
	flatpak-builder --force-clean --repo=_repo _build platform-info.json
	flatpak-builder --run _build platform-info.json platform-info

