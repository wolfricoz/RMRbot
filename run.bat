
set API=TRUE

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

python -m uvicorn main:app --port=8083
