# -*- coding: utf-8 -*-
"""DBSI_UniversityRecommendationSystem.ipynb

Automatically generated by Colaboratory.
Original file is located at
    https://colab.research.google.com/drive/1zz4WQdgJk6wOUtixxV43ZuyZRE4enZOJ

Converts data into Pandas dataframe. Cleans, pre-process and encode the data as required by the model.
Handles nulls and dirty values. Trains models and determines model accuracy.
"""

# Commented out IPython magic to ensure Python compatibility.
import pandas as pd
import numpy as np
import pickle
from sklearn import preprocessing

le = preprocessing.LabelEncoder()
# lists required to store the encoded values
mapping_major = {}
mapping_specialization = {}
mapping_program = {}

mapping_department = {}
mapping_termAndYear = {}
mapping_cgpaScale = {}
mapping_univName = {}

import warnings
warnings.filterwarnings('ignore')

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LinearRegression
from sklearn.feature_selection import RFE
from sklearn.metrics import r2_score
pd.set_option('display.float_format', lambda x:'%.5f' % x)



"""Explores the data obtaines after converting into Pandas dataframe
"""
def data_exploration():

    data = pd.read_csv("university_data.csv")
    data.head(15)
    data.shape
    data.describe()
    data.nunique()
    data.isnull().sum()
    data.info()
    data_cleanup(data)


"""This method handles null values. Replaces the dirty values with empty strings.
Replaces the empty strings with the median value of respective columns
Returns: 
the updated dataframe
dataframe storing only numeric data types
dataframe storing only string data types
"""
def data_cleanup():
    data = pd.read_csv("university_data.csv")
    # dropping unwanted columns
    data = data.drop(['userName', 'topperCgpa', 'userProfileLink', 'gmatA', 'gmatV', 'gmatQ', 'toeflEssay'], axis=1)

    # replacing dirty values with NaN
    data.loc[data.confPubs == 'Fall - 2015', 'confPubs'] = np.NAN
    data.loc[data.confPubs == 'Fall - 2012', 'confPubs'] = np.NAN
    data.loc[data.confPubs == 'Fall - 2014', 'confPubs'] = np.NAN
    data.journalPubs = data.journalPubs.apply(lambda x: np.NAN if 'http://www' in str(x) else x)

    # storing numerical fields in a variable
    numeric_data= data[['researchExp', 'industryExp', 'toeflScore', 'internExp', 'greV', 'confPubs', 'greQ', 'greA', 'journalPubs', 'cgpa', 'cgpaScale', 'admit']].copy()

    # replacing NaN values with median values for respective columns
    for col in numeric_data:
      numeric_data[col].fillna(data[col].median(), inplace = True)

    # storing string fields in a variable
    string_data = data[['major', 'specialization', 'program', 'department', 'termAndYear', 'ugCollege', 'univName']]

    # replacing NaN values with median values for respective columns
    for col in string_data:
      data_key = string_data[col].value_counts().keys()
      string_data[col] = data[col].fillna('')
      string_data.loc[string_data[col] == '', col] = data_key[0]
      string_data.loc[string_data[col] == '0', col] = data_key[0]
    data = pd.concat([numeric_data, string_data], axis=1, join="inner")
    # group_data_category(data)
    return data, numeric_data, string_data



"""This method groups categories of data with smaller frequencies into a single category.
Returns: updated data
"""
def group_data_category(data):
    # grouping data from speciliazation column
    threshold_percent = 0.5

    series = pd.value_counts(data['specialization'])
    mask = (series / series.sum() * 100).lt(threshold_percent)
    data = data.assign(specialization_updated = np.where(data['specialization'].isin(series[mask].index),
                                                         'Other', data['specialization']))

    # grouping data from major column
    threshold_percent = 0.5

    series = pd.value_counts(data['major'])
    mask = (series / series.sum() * 100).lt(threshold_percent)
    data = data.assign(major_updated = np.where(data['major'].isin(series[mask].index),'Other', data['major']))

    # grouping data from department column
    threshold_percent = 0.5

    series = pd.value_counts(data['department'])
    mask = (series / series.sum() * 100).lt(threshold_percent)
    data = data.assign(department_updated = np.where(data['department'].isin(series[mask].index),'Other', data['department']))

    threshold_percent = 0.5

    series = pd.value_counts(data['termAndYear'])
    mask = (series / series.sum() * 100).lt(threshold_percent)
    data = data.assign(termAndYear_updated = np.where(data['termAndYear'].isin(series[mask].index),
                                                      'Other', data['termAndYear']))

    # string_data.termAndYear_updated.value_counts()

    data = data.drop(['major', 'specialization', 'department', 'termAndYear'], axis=1)
    data = data.rename(columns={"specialization_updated": "specialization", "major_updated": "major",
                                "department_updated": "department", "termAndYear_updated": "termAndYear"})
    # data_encoding(data)
    return data



"""Encoding categorical data as various classificaton algorithms cannot work on categorial data.
Used Label Encoder to encode data
Returns: the label encoded columns
"""
def data_encoding(data):
    data['major'] = le.fit_transform(data.major.values)
    mapping_major = dict(zip(le.classes_, range(len(le.classes_))))
    data['specialization'] = le.fit_transform(data.specialization.values)
    mapping_specialization = dict(zip(le.classes_, range(len(le.classes_))))
    data['program'] = le.fit_transform(data.program.values)
    mapping_program = dict(zip(le.classes_, range(len(le.classes_))))
    data['department'] = le.fit_transform(data.department.values)
    mapping_department = dict(zip(le.classes_, range(len(le.classes_))))

    data['termAndYear'] = le.fit_transform(data.termAndYear.values)
    mapping_termAndYear = dict(zip(le.classes_, range(len(le.classes_))))

    data['univName'] = le.fit_transform(data.univName.values)
    mapping_univName = dict(zip(le.classes_, range(len(le.classes_))))
    # build_model(data)
    return  mapping_major,mapping_specialization, mapping_program, mapping_department, mapping_termAndYear, \
            mapping_univName



"""Reverse encoding the label encoded column values.
"""
def reverse_encoding(element, dictionary):
    value = dictionary.get(element)
    return value



"""Selects the dependant and target variable.
Splits the data for trainng and testing purposes
Calls the Decision Tree Classifier to train the data"""
def build_model(data):
    # selecting x and y values for model training
    # x values are independant values.
    # y values are the dependant values
    x = data.iloc[:, [1,2,3,4,5,6,7,8,9,10,12,14,15,17,18]]
    y = data.iloc[:, [11]]

    """## Splitting data into training and testing data"""

    from sklearn.model_selection import train_test_split
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=83)
    decision_tree(x_train, x_test, y_train, y_test)



"""Implementing the Logistic Regression
Determines model accuracy"""
def logistic_regression(x_train, x_test, y_train, y_test):
    from sklearn.preprocessing import OneHotEncoder,StandardScaler
    from sklearn.pipeline import make_pipeline
    from sklearn.linear_model import LogisticRegression
    scaler = StandardScaler()

    lr = LogisticRegression()
    pipe_lr = make_pipeline(scaler, lr)
    pipe_lr.fit(x_train, y_train)
    y_pred = pipe_lr.predict(x_test)

    from sklearn.metrics import accuracy_score
    accuracy_score(y_pred, y_test)
    pickle.dump(pipe_lr, open('LogisticRegressionModel.pkl', 'wb'))



"""Implementing the Naive Bayes Classification algorithm
Determines model accuracy"""
def naive_bayes(x_train, x_test, y_train, y_test):
    from sklearn.preprocessing import OneHotEncoder,StandardScaler
    from sklearn.pipeline import make_pipeline

    from sklearn.naive_bayes import GaussianNB
    scaler = StandardScaler()

    nb = GaussianNB()
    pipe_nb = make_pipeline(scaler, nb)
    pipe_nb.fit(x_train, y_train)
    y_pred = pipe_nb.predict(x_test)

    from sklearn.metrics import accuracy_score
    accuracy_score(y_pred, y_test)
    pickle.dump(pipe_nb, open('NaiveBayesModel.pkl', 'wb'))



"""Implementing the Random forest Classification algorithm
Determines model accuracy"""
def random_forest(x_train, x_test, y_train, y_test):
    from sklearn.preprocessing import OneHotEncoder,StandardScaler
    from sklearn.pipeline import make_pipeline
    from sklearn.ensemble import RandomForestClassifier
    scaler = StandardScaler()
    from sklearn import metrics

    rfc = RandomForestClassifier()
    pipe_rfc = make_pipeline(scaler, rfc)
    pipe_rfc.fit(x_train, y_train)
    y_pred = pipe_rfc.predict(x_test)

    from sklearn.metrics import classification_report
    from sklearn.metrics import accuracy_score
    accuracy_score(y_pred, y_test)
    pickle.dump(pipe_rfc, open('RandomForestClassifierModel.pkl', 'wb'))


"""Implementing the K Neighbors Classifier algorithm
Determines model accuracy"""
def nearest_neighbours(x_train, x_test, y_train, y_test):
    from sklearn.preprocessing import OneHotEncoder,StandardScaler
    from sklearn.pipeline import make_pipeline
    from sklearn.neighbors import KNeighborsClassifier
    scaler = StandardScaler()

    knn = KNeighborsClassifier(n_neighbors=4)
    pipe_knn = make_pipeline(scaler, knn)
    pipe_knn.fit(x_train, y_train)
    y_pred = pipe_knn.predict(x_test)

    from sklearn.metrics import accuracy_score
    accuracy_score(y_pred, y_test)
    pickle.dump(pipe_knn, open('KNearestClassifierModel.pkl', 'wb'))


"""Implementing the Decision Tree Classifier algorithm
Determines model accuracy
Stores the model in a pickle file"""
def decision_tree(x_train, x_test, y_train, y_test):
    from sklearn.preprocessing import OneHotEncoder,StandardScaler
    from sklearn.pipeline import make_pipeline
    from sklearn.tree import DecisionTreeClassifier
    scaler = StandardScaler()

    dtc = DecisionTreeClassifier()
    pipe_dtc = make_pipeline(scaler, dtc)
    pipe_dtc.fit(x_train, y_train)
    y_pred = pipe_dtc.predict(x_test)
    from sklearn.metrics import accuracy_score
    print(accuracy_score(y_pred, y_test))
    pickle.dump(pipe_dtc, open('DecisionTreeModel.pkl', 'wb'))



if __name__ == '__main__':
  data_cleanup()


