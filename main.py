"""DBSI_UniversityRecommendationSystem.ipynb
Establishes connection with simpleDB database.
Trained model predicts chances and submits data to database.
"""

from _csv import reader
import pandas as pd
import boto3
from flask import Flask, render_template, request, app, abort
import pickle
from DataCleaningAndProcessing import data_cleanup, group_data_category, build_model, \
    reverse_encoding, data_encoding
AWS_REGION = 'us-east-1'
ACCESS_KEY_ID = 'AKIA345V3YS6WKLF5M5S'
ACCESS_KEY = 'IVrnJSAYovUQMl2BfqQtQNXndpHjq6lmnX8RRf5I'
DOMAIN_NAME = "University"


app = Flask(__name__)

# trained model
pipe = pickle.load(open("DecisionTreeModel.pkl", 'rb'))

class items:
    Item = 1467


"""This method calls the methods required to clean and pre-process the data.
It renders the HTML template.
"""
@app.route("/")
def index():
    clean_data, numeric_data, string_data = data_cleanup()
    # storing numerical fields in a variable
    # formatted_data = group_data_category(clean_data)
    grouped_data = group_data_category(clean_data)
    major = sorted(grouped_data['major'].unique())
    specialization = sorted(grouped_data['specialization'].unique())
    program = sorted(grouped_data['program'].unique())
    department = sorted(grouped_data['department'].unique())
    termAndYear = sorted(grouped_data['termAndYear'].unique())
    cgpaScale = sorted(grouped_data['cgpaScale'].unique())
    univName = sorted(grouped_data['univName'].unique())

    index.d1, index.d2, index.d3, index.d4, index.d5, index.d6 = data_encoding(grouped_data)
    return render_template('index.html', major=major, specialization=specialization, program=program,
                           department=department, termAndYear=termAndYear, cgpaScale=cgpaScale, univName=univName)


"""Stores input received from the user interface in a list
Return: list
"""
def takeData():
    major = request.form.get('major')
    major_decoded = reverse_encoding(major, index.d1)
    indexp = request.form.get('indexp')
    specialization = request.form.get('specialization')
    specialization_decoded = reverse_encoding(specialization, index.d2)
    grev = request.form.get('grev')
    greq = request.form.get('greq')
    grea = request.form.get('grea')
    toefl = request.form.get('toefl')
    program = request.form.get('program')
    program_decoded = reverse_encoding(program, index.d3)
    internExp = request.form.get('internExp')
    journals = request.form.get('journals')
    tey = request.form.get('tey')
    tey_decoded = reverse_encoding(tey, index.d5)
    conpub = request.form.get('conpub')
    cgpa = request.form.get('cgpa')
    cgpascale = request.form.get('cgpascale')
    university = request.form.get('university')
    university_decoded = reverse_encoding(university, index.d6)

    researchexp = request.form.get('researchexp')
    department = request.form.get('department')
    admituniv_1 = request.form.get('admituniv_1')
    admituniv_2 = request.form.get('admituniv_2')

    list = [major_decoded, indexp, specialization_decoded, grev, greq, grea, toefl, program_decoded,
            internExp, journals, tey_decoded, conpub, cgpa, cgpascale, university_decoded,
            major, researchexp, department, admituniv_1, admituniv_2, specialization, program, tey]
    return list


"""Outputs the prediction based on the user input values.
Return: predicted output in integer encoded format
"""
@app.route('/predict', methods=['POST'])
def predict():
    list = takeData()
    input = pd.DataFrame([[list[0], list[1], list[2], list[3], list[4], list[5], list[6],
                           list[7], list[8], list[9],
                           list[10], list[11], list[12], list[13], list[14]]],
                         columns=['major', 'industryExp', 'specialization', 'greV', 'greQ', 'greA',
                                  'toeflScore', 'program', 'internExp', 'journalPubs', 'termAndYear',
                                  'confPubs', 'cgpa', 'cgpaScale', 'univName'])

    prediction = pipe.predict(input)[0]
    result = prediction
    return str(result)


"""Stores input received from the user interface in a list.
Uploads the received data into simpleDB
"""
@app.route('/upload', methods=['POST'])
def upload_data():
    list = takeData()

    l = ['major', list[15], "researchExp", list[16], "industryExp", list[1], "specialization", list[20],
         "toeflScore", list[5], "program", list[21], "department", list[17], "internExp", list[8], "greV", list[3],
         "greQ", list[4], "journalPubs", list[9], "greA", list[6], "termAndYear", list[22], "confPubs", list[11],
         "cgpa", list[12], "cgpaScale", list[13], "univName", list[18], "univName", list[19], "admit", "1"]
    i = 0


    while i in range(len(l)):
        column_name = l[i]
        value = l[i + 1]
        put_attribute_to_db(column_name, value, str(items.Item))
        i = i + 2
    items.Item = items.Item+1
    return


def put_attribute_to_db(column_name, value, item, conn=None):
    if conn is None:
        conn = get_connection()
    conn.put_attributes(
        DomainName= DOMAIN_NAME,
        ItemName=item,
        Attributes=[
            {
                'Name': column_name,
                'Value': value,
            },
        ]
    )


def get_connection():
    conn = boto3.client('sdb', region_name=AWS_REGION, aws_access_key_id=ACCESS_KEY_ID,
                        aws_secret_access_key=ACCESS_KEY)
    return conn


def import_csv(conn, filename):
    if conn is None:
        conn = get_connection()
    with open(filename, 'r') as csv:
        csv_read = reader(csv)
        header = next(csv_read)
        if header is not None:
            item = 1
            for row in csv_read:
                for i in range(len(row)):
                    put_attribute_to_db(conn, str(item), header[i], row[i])
                item += 1


def create_domain(conn=None):
    if conn is None:
        conn = get_connection()
    response = conn.create_domain(
        DomainName=DOMAIN_NAME
    )


def delete_attribute(conn=None):
    if conn is None:
        conn = get_connection()
    response = conn.delete_attributes(
        DomainName=DOMAIN_NAME,
        ItemName='5405',

    )

def select(conn=None):
    response = conn.select(
        SelectExpression='select * from University',
    )


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    app.run(debug=True, port=5000)
