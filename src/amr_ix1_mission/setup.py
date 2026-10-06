from setuptools import find_packages, setup

package_name = 'amr_ix1_mission'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/config', ['config/inspection_waypoints.yaml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='hossam',
    maintainer_email='hossamsalhinahmed@gmail.com',
    description='Mission-level waypoint recording and inspection workflow for AMR-IX1',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'waypoint_recorder = amr_ix1_mission.waypoint_recorder:main',
            'inspection_mission = amr_ix1_mission.inspection_mission:main',
        ],
    },
)
