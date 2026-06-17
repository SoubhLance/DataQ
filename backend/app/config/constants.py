from enum import Enum

class MissingStrategy(str, Enum):
    MEAN = "mean"
    MEDIAN = "median"
    MODE = "mode"
    CONSTANT = "constant"
    DROP = "drop"

class OutlierMethod(str, Enum):
    IQR = "iqr"
    ZSCORE = "zscore"
    ISOLATION_FOREST = "iforest"

class OutlierAction(str, Enum):
    REMOVE = "remove"
    CAP = "cap"
    KEEP = "keep"

class ScalingMethod(str, Enum):
    STANDARD = "standard"
    MINMAX = "minmax"
    ROBUST = "robust"

class EncodingMethod(str, Enum):
    LABEL = "label"
    ONEHOT = "onehot"

class DataType(str, Enum):
    INT = "int"
    FLOAT = "float"
    STRING = "string"
    DATETIME = "datetime"
