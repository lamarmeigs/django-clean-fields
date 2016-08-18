from setuptools import find_packages, setup


# PyPI parses ReStructuredText only, so convert the markdown README file.
try:
    import pypandoc
    long_description = pypandoc.convert_file('README.md', 'rst')
except ImportError:
    long_description = open('README.md', 'r').read()


setup(
    name='django-clean-fields',
    version='0.3.0',
    url='https://github.com/lamarmeigs/django-clean-fields',
    author='Lamar Meigs',
    author_email='lamarmeigs@gmail.com',
    license='MIT',
    description='A Django utility to clean model field values on save.',
    long_description=long_description,
    packages=find_packages(exclude=['tests']),
    install_requires=['Django>=1.7'],
    test_suite='run_tests.run_tests',
    tests_require=['mock==2.0.0'],
    zip_safe=True,
    keywords='django, model, field, validation',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.7',
        'Framework :: Django :: 1.8',
        'Framework :: Django :: 1.9',
        'Framework :: Django :: 1.10',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
