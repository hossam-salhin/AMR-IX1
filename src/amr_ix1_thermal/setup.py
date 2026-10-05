from setuptools import find_packages, setup

package_name = 'amr_ix1_thermal'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        (
            'share/ament_index/resource_index/packages',
            ['resource/' + package_name],
        ),
        (
            'share/' + package_name,
            ['package.xml'],
        ),
        (
            'share/' + package_name + '/launch',
            ['launch/thermal_visualizer.launch.py'],
        ),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='hossam',
    maintainer_email='hossamsalhinahmed@gmail.com',
    description='Thermal camera visualization for AMR-IX1',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'thermal_visualizer = amr_ix1_thermal.thermal_visualizer:main',
        ],
    },
)
