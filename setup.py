from setuptools import setup, find_packages

setup(
    name='customer_statement',
    version='0.0.1',
    description='Accounting Customer Statement Report',
    author='SurgiShop',
    author_email='gary.starr@surgishop.com',
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=['frappe']
)
