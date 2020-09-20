import os

from setuptools import find_packages, setup

install_requires = [
    line.rstrip()
    for line in open(os.path.join(os.path.dirname(__file__), "requirements.txt"))
]

setup(
    name="calciumcurator",
    install_requires=install_requires,
    version="0.0.1",
    description="An GUI for curating calcium imaging results",
    url="https://github.com/donatolab/calciumcurator",
    license="GPL",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "calciumcurator=calciumcurator.__main__:main",
            "view-caiman=calciumcurator.view_cli:view_caiman",
        ]
    },
    zip_safe=False,
)
