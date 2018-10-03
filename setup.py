
from setuptools import setup, find_packages

DEPENDENCIES = [
    "anthill-common"
]

setup(
    name='anthill-report',
    package_data={
      "anthill.report": ["anthill/report/sql", "anthill/report/static"]
    },
    setup_requires=["pypigit-version"],
    git_version="0.1.0",
    description='User submitted reports collecting service',
    author='desertkun',
    license='MIT',
    author_email='desertkun@gmail.com',
    url='https://github.com/anthill-platform/anthill-report',
    namespace_packages=["anthill"],
    packages=find_packages(),
    zip_safe=False,
    install_requires=DEPENDENCIES
)
