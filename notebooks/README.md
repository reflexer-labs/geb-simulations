# Jupytext Paired Notebooks

Jupytext allows us to create a notebook paired with a Python script, to more easily keep track of updates, and execute simulation notebooks. In the `notebooks/` directory, check if their is both an `.ipynb` and `.py` file for a notebook, then use the following command to sync the two files when necessary:

```
# Initialize paired ipynb/py notebook: `jupytext --set-formats ipynb,py:percent notebooks/notebook.ipynb`
jupytext --sync --update notebooks/notebook.ipynb
```
