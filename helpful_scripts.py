import os, sys

# handle print
class HiddenPrints:
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = open(os.devnull, "w", encoding="utf-8")

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = self._original_stdout


def get_matrix(df, x_name, y_name, value_name):
    """get matrix from a pandas dataframe

    Args:
        df (pandas dataframe): _description_
        x_name (str): colume name of x_axis
        y_name (str): colume name of y_axis
        value_name (str): colume name of value

    Returns:
        _type_: _description_
    """

    df_matrix = df.pivot_table(columns=x_name, index=y_name, values=value_name)
    try:
        df_matrix.index = df_matrix.index.astype(str)
        df_matrix.columns = df_matrix.columns.astype(str)
    except:
        pass

    return df_matrix
