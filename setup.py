from setuptools import find_packages, setup

setup(
    name="legal_doc_intelligence",
    version="1.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "sqlalchemy>=1.4.0",
        "loguru>=0.6.0",
        "numpy>=1.21.0",
        "pandas>=1.3.0",
        "fastapi>=0.68.0",
        "uvicorn>=0.15.0",
        "pytest>=6.2.5",
        "pytest-cov>=2.12.0",
        "pytest-asyncio>=0.21.0",
    ],
    python_requires=">=3.8",
)
