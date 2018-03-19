from setuptools import setup

setup(name='CoReSyF tools',
      version='0.2',
      description='base classes for CoReSyF tool',
      packages=['coresyftools'],
      install_requires=[
            'cerberus',
            'click',
            'sarge'
      ],
      test_suite='nose.collector',
      tests_require=['nose'])
