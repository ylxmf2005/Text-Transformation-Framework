# post process
poetry run python -m seceval.main  -t d3fend -n -1 -p 
poetry run python -m seceval.main  -t attck -n -1 -p 
poetry run python -m seceval.main  -t owasp_wstg -n -1 -p 
poetry run python -m seceval.main  -t owasp_mastg -n -1 -p 
poetry run python -m seceval.main  -t cs161_textbook -n -1 -p 
poetry run python -m seceval.main  -t mozilla_security -n -1 -p 
poetry run python -m seceval.main  -t mit6.858 -n -1 -p 
poetry run python -m seceval.main  -t cwe -n 200  -p 
poetry run python -m seceval.main -t windows_security -n 100 -p  
poetry run python -m seceval.main -t android_sec_doc -n 100 -p  
poetry run python -m seceval.main -t apple_platform_security  -n 73 -p 