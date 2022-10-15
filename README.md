# req2flatpak

A script to convert python package requirements to flatpak build manifests.

## Intended Use

The `req2flatpak.py` script is meant for programmers who want to package a python application using flatpak.

The script takes python package requirements as input, e.g., as `requirements.txt` file.
It allows to specify the target platform's python version and architecture.
The script outputs an automatically generated `flatpak-builder` build module.
The manifest, if included into a flatpak build, will install the python packages using pip.

## Installation

The simplest installation method is to download the `req2flatpak.py` script and to run it on your computer.

Alternatively, you can clone the git repository and run the script there.

## Commandline Interface

You can generate a `flatpak-builder` build module like this:

```bash
req2flatpak.py --requirements-file requirements.txt --target-platforms 310-x86_64 310-aarch64
```

When invoked like this, req2flatpak will read the requirements file, query pypi about available downloads, choose appropriate downloads for the specified target platforms, and generate a flatpak-builder build module.

Note that req2flatpak will not resolve transitive dependencies or freeze dependency versions. Use other tools like [pip-compile](https://pypi.org/project/pip-tools/) or [poetry](https://pypi.org/project/poetry/) for this purpose and generate/export a full resolved requirements.txt file using these tools.

Run `req2flatpak.py --help` to learn more about available commandline options.

## Advanced Usage

You can write a custom python script to tweak and tune the behavior as needed. You can have a look at how the `main()` method is implemented, it is really not that complicated. The workflow basically boils down to:

```python3
requirements = RequirementsParser.parse_file("requirements.txt")
platforms = [PlatformFactory.from_string("310-x86_64")]
releases = PypiClient.get_releases(requirements)
downloads = {
    DownloadChooser.wheel_or_sdist(release, platform)
    for release in releases
    for platform in platforms
}
manifest = FlatpakGenerator.manifest(requirements, downloads)
```

Writing a custom script gives you all the freedom to modify each of these steps as you see fit. For example, in your custom script, you may want to query other package indices instead of pypi. You may prefer wheels or sdists for certain packages. You may want to exclude specific packages. All of this can be freely implemented in a custom script. Of course, you can also fork and modify req2flatpak, feel free to modify.

## Contributing

req2flatpak is developed in an open-source, community-driven way, as a voluntary effort in the authors' free time.

All contributions are greatly appreciated... pull requests are welcome, and so are bug reports and suggestions for improvement. See [CONTRIBUTING.md](./CONTRIBUTING.md) for details, e.g., how to setup a development environment.

## Related Work

The [flatpak-pip-generator](https://github.com/flatpak/flatpak-builder-tools/blob/master/pip/flatpak-pip-generator) script is part of a larger suite of [flatpak-builder-tools](https://github.com/flatpak/flatpak-builder-tools).
The `flatpak-pip-generator` script is very similar to this project - both scripts basically do the same thing, and this project took a lot of inspiration from flatpak-pip-generator.
In fact, this project was created when we discussed a feature request [#296](https://github.com/flatpak/flatpak-builder-tools/issues/296) in flatpak-pip-generator and when I (johannesjh) decided to re-implement a new prototype from scratch.

Comparison between `flatpak-pip-generator` and `req2flatpak.py`: Each of the two project likely has its own benefits and a comparison between the two will likely change over time. As in Oct, 2022, in my personal opinion (johannesjh), I see the following differences:

- Both projects generate build modules for flatpak-builder.
- Both projects consist of a single script file with minimal dependencies, and are thus very easy to install.
- `flatpak-pip-generator` resolves dependencies and freezes dependency versions, whereas `req2flatpak.py` asks the user to provide a fully resolved list of dependencies with frozen dependency versions.
- `flatpak-pip-generator` is older and thus likely to be more mature. It supports more commandline options and probably has a more complete feature set.
- `req2flatpak.py` is faster. The script itself runs faster because it does not need to download package files in order to generate the manifest. And the flatpak build runs faster because all packages (from the entire `requirements.txt` file) are installed in a single call to `pip install`.
- `req2flatpak.py` re-implements some functionality of pip. In contrast, `flatpak-pip-generator` uses pip's official functionality. Specifically, `req2flatpak.py` re-implements how pip queries available downloads from pypi and how pip chooses suitable downloads to match a given target platform.
- `req2flatpak.py` prefers binary wheels, whereas `flatpak-pip-generator` prefers source packages.

## License

req2flatpak is MIT-licensed, see the [COPYING](./COPYING) file.
