import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()

setup(
    name='django-avishan',
    version='0.2.3',
    packages=find_packages(),
    description='Avishan is just an set of tools',
    long_description=README,
    author='Morteza Afshari',
    author_email='afshari9978@gmail.com',
    url='https://gitlab.com/afshari9978/avishan',
    license='MIT',
    install_requires=[
        'bcrypt==3.1.7',
        'Django==3.0.3',
        'django-cors-headers==3.2.1',
        'Khayyam==3.0.17',
        'gunicorn==20.0.4',
        'Pillow==7.0.0',
        'PyJWT==1.7.1',
        'requests==2.22.0',
        'stringcase==1.2.0',
    ]
)
