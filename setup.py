import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()

setup(
    name='django-avishan',
    version='0.1.11',
    packages=find_packages(),
    description='Avishan is a set of tools for building fast, comfortable and reliable django apps',
    long_description=README,
    author='Morteza Afshari',
    author_email='afshari9978@gmail.com',
    url='https://gitlab.com/afshari9978/avishan',
    license='MIT',
    install_requires=[
        'Django>=2.2.5',
        'avishan_wrapper==0.1.0',
        'django-cors-headers==2.4.0',
        'gunicorn==19.9.0',
        'kavenegar==1.1.2',
        'Khayyam==3.0.17',
        'Pillow==6.0.0',
        'PyJWT==1.7.0'
    ]
)