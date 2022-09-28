from setuptools import find_packages, setup

setup(
    name='boxlet',
    description='A set of scripts for pygame.',
    version='0.0.0',
    url='https://github.com/Werxzy/boxlet',
    license='MIT',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'pygame',
        'numpy',
        'pyopengl',
    ],
    extras_require={'extras': [
        'pyopengl-accelerate',
        ],
    },
    python_requires='>=3.6',
)
