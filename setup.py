from setuptools import setup, find_packages

setup(
    name="git_commit",
    version="0.2",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.1",
        "tiktoken>=0.8.0"
        
    ],
    entry_points={
        'console_scripts': [
            'git_commit = git_commit.cli:main',
        ],
    },
    author="Spine Zhang",
    author_email="zhangyubin@bicv.com",
    description="A CLI tool for git comments",
    keywords="git git_commit tool",
)