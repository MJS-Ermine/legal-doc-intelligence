@echo off
:: 建立 Python 虛擬環境
python -m venv venv

:: 啟動虛擬環境
call .\venv\Scripts\activate

:: 建立資料夾結構
mkdir src
mkdir data
mkdir tests
mkdir scripts
mkdir docs
mkdir examples
mkdir .vscode

:: 初始化 Git 儲存庫
git init

:: 建立空的必要檔案
type nul > README.md
type nul > requirements.txt
type nul > .gitignore
type nul > .vscode\settings.json

:: 寫入 .gitignore 的內容
echo # Byte-compiled / optimized / DLL files > .gitignore
echo __pycache__/ >> .gitignore
echo *.py[cod] >> .gitignore
echo *$py.class >> .gitignore
echo. >> .gitignore
echo # C extensions >> .gitignore
echo *.so >> .gitignore
echo. >> .gitignore
echo # Distribution / packaging >> .gitignore
echo .Python >> .gitignore
echo build/ >> .gitignore
echo develop-eggs/ >> .gitignore
echo dist/ >> .gitignore
echo downloads/ >> .gitignore
echo eggs/ >> .gitignore
echo .eggs/ >> .gitignore
echo lib/ >> .gitignore
echo lib64/ >> .gitignore
echo parts/ >> .gitignore
echo sdist/ >> .gitignore
echo var/ >> .gitignore
echo wheels/ >> .gitignore
echo pip-wheel-metadata/ >> .gitignore
echo share/python-wheels/ >> .gitignore
echo *.egg-info/ >> .gitignore
echo .installed.cfg >> .gitignore
echo *.egg >> .gitignore
echo. >> .gitignore
echo # PyInstaller >> .gitignore
echo *.manifest >> .gitignore
echo *.spec >> .gitignore
echo. >> .gitignore
echo # Installer logs >> .gitignore
echo pip-log.txt >> .gitignore
echo pip-delete-this-directory.txt >> .gitignore
echo. >> .gitignore
echo # Unit test / coverage reports >> .gitignore
echo htmlcov/ >> .gitignore
echo .tox/ >> .gitignore
echo .nox/ >> .gitignore
echo .coverage >> .gitignore
echo .coverage.* >> .gitignore
echo .cache >> .gitignore
echo nosetests.xml >> .gitignore
echo coverage.xml >> .gitignore
echo *.cover >> .gitignore
echo .hypothesis/ >> .gitignore
echo .pytest_cache/ >> .gitignore
echo. >> .gitignore
echo # Translations >> .gitignore
echo *.mo >> .gitignore
echo *.pot >> .gitignore
echo. >> .gitignore
echo # Django stuff >> .gitignore
echo *.log >> .gitignore
echo local_settings.py >> .gitignore
echo db.sqlite3 >> .gitignore
echo db.sqlite3-journal >> .gitignore
echo. >> .gitignore
echo # Flask stuff >> .gitignore
echo instance/ >> .gitignore
echo .webassets-cache >> .gitignore
echo. >> .gitignore
echo # Scrapy stuff >> .gitignore
echo .scrapy >> .gitignore
echo. >> .gitignore
echo # Sphinx documentation >> .gitignore
echo docs/_build/ >> .gitignore
echo. >> .gitignore
echo # PyBuilder >> .gitignore
echo target/ >> .gitignore
echo. >> .gitignore
echo # Jupyter Notebook >> .gitignore
echo .ipynb_checkpoints >> .gitignore
echo. >> .gitignore
echo # pyenv >> .gitignore
echo .python-version >> .gitignore
echo. >> .gitignore
echo # celery beat schedule file >> .gitignore
echo celerybeat-schedule >> .gitignore
echo. >> .gitignore
echo # SageMath parsed files >> .gitignore
echo *.sage.py >> .gitignore
echo. >> .gitignore
echo # Environments >> .gitignore
echo .env >> .gitignore
echo .venv >> .gitignore
echo env/ >> .gitignore
echo venv/ >> .gitignore
echo ENV/ >> .gitignore
echo env.bak/ >> .gitignore
echo venv.bak/ >> .gitignore
echo. >> .gitignore
echo # Spyder project settings >> .gitignore
echo .spyderproject >> .gitignore
echo .spyproject >> .gitignore
echo. >> .gitignore
echo # Rope project settings >> .gitignore
echo .ropeproject >> .gitignore
echo. >> .gitignore
echo # mkdocs documentation >> .gitignore
echo /site >> .gitignore
echo. >> .gitignore
echo # mypy >> .gitignore
echo .mypy_cache/ >> .gitignore
echo .dmypy.json >> .gitignore
echo dmypy.json >> .gitignore
echo. >> .gitignore
echo # Pyre type checker >> .gitignore
echo .pyre/ >> .gitignore

:: 寫入 VSCode 設定的內容
echo { > .vscode\settings.json
echo     "python.pythonPath": "./venv/Scripts/python.exe" >> .vscode\settings.json
echo } >> .vscode\settings.json

:: 完成訊息
echo Python 專案資料夾已成功建立！
