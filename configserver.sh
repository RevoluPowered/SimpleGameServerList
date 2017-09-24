# install pipenv
pip install pipenv
# install this project's dependencies
pipenv install
echo "Installing for deployment systemwide!"
sudo pipenv install --system
