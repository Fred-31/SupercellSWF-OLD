import setuptools



description = "Editing tool (read/write) .sc files (*_tes.sc , *.sc, *_dl.sc ) from Supercell games (Brawl Stars, Clash Royale, Clash of Clans and others)."
long_description = description


with open("README.md", 'r') as readme:
    long_description = readme.read()
    readme.close()

with open("requirements.txt", 'r') as requires:
    requirements = requires.read().split("\n")


setuptools.setup(
    name="SupercellSWF",
    version="0.1.0.5",
    author="Fred31-pavel-sokov",
    author_email="fred20rus@gmail.com",
    description=description,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Fred31-pavel-sokov/SupercellSWF",
    license="GPLv3",
    packages=setuptools.find_packages(),
    install_requires=requirements,
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.8'
)
