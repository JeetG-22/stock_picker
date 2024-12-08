# stock_picker: CS210 Project
Predicting Top 5 Tech Stocks To Buy

### Create Python Virtual Environment
In this project, we utilized Python virtual enviroments to keep pip packages consistent across all machines. 

To create it, we use:
```shell
bash create_venv.sh
```

which implicitly runs:
```shell
python -m venv ../venv
source venv/bin/activate
pip install -r ../requirements.txt
```

If we want to update the requirements.txt file with the packages that we've installed with pip thus far, we can run:
```shell
pip freeze > requirements.txt
```

and then if we need to update the requirements again later:
```shell
pip install -r requirements.txt
```


