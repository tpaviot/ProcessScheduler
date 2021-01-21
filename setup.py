from setuptools import find_packages, setup

DESCRIPTION = (
      'A python package to formulate and solve resource-constrained scheduling problems'
)

CLASSIFIERS = [
      'Development Status :: 3 - Alpha',
      'Intended Audience :: Developers',
      'Intended Audience :: Manufacturing',
      'Intended Audience :: Financial and Insurance Industry',
      'Intended Audience :: Healthcare Industry',
      'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
      'Natural Language :: English',
      'Operating System :: OS Independent',
      'Programming Language :: Python :: 3',
      'Topic :: Office/Business :: Scheduling',
      'Topic :: Software Development :: Libraries',
      'Typing :: Typed'
]

setup(name='ProcessScheduler',
      version='0.2.0-dev',
      description=DESCRIPTION,
      long_description=open("README.md").read(),
      long_description_content_type="text/markdown",
      url='https://github.com/tpaviot/ProcessScheduler',
      author='Thomas Paviot',
      author_email='tpaviot@gmail.com',
      license='GPLv3',
      platforms="Platform Independent",
      packages=find_packages(),
      install_requires=['z3-solver==4.8.10.0'],
      classifiers=CLASSIFIERS,
      zip_safe=True)
