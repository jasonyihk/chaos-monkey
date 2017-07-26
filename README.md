### Prerequisite 
```sh
Python 3.5

Pip3

curl https://bootstrap.pypa.io/get-pip.py | python3
```

### Install python version management
```sh
brew install pyenv

pyenv install 3.5.0

pyenv local 3.5.0

```

### Install chaos related related modules
```sh
pip3 install -r requirements.txt
```

### Build container
```sh
docker build -t chaos-monkey:latest .
```

### Deploy to kubernetes
```sh
kubectl -n testing apply -f kube/
```

