from setuptools import setup, find_packages
import os

version = '1.0'

tests_require = [
    'Products.Silva [test]',
    ]

setup(name='silva.security.renameusers',
      version=version,
      description="Rename users identifier in a Silva site",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      classifiers=[
        "Framework :: Zope2",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='silva cms zope security rename users',
      author='Infrae',
      author_email='info@infrae.com',
      url='http://infrae.com/products/silva',
      license='BSD',
      package_dir={'': 'src'},
      packages=find_packages('src', exclude=['ez_setup']),
      namespace_packages=['silva', 'silva.security'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
        'Products.Silva',
        'five.grok',
        'setuptools',
        'silva.core.conf',
        'silva.core.services',
        'zeam.form.silva',
        'zope.interface',
        'zope.schema',
        ],
      tests_require = tests_require,
      extras_require = {'test': tests_require},
      )
