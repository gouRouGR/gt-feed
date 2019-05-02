import setuptools

with open("README.md", "r") as f:
	long_description = f.read()

setuptools.setup(
	name="gtfeed",
	version="0.0.1",
	author="George Mantakos",
	description="Detect new torrent releases on the Greek-Team.cc tracker and perform some action ",
	long_description=long_description,
	long_description_content_type="text/markdown",
	url="https://github.com/geomsk/gt-feed",
	packages=setuptools.find_packages(),
	classifiers=[
		"Programming Language :: Python :: 3",
		"License :: OSI Approved :: GNU Affero General Public License v3",
		"Operating System :: OS Independent",
	],
	scripts=["bin/gt-feed"],
	install_requires=[
		"requests",
		"peewee",
		"pyyaml"
	],
)
