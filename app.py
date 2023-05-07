from flask import Flask, render_template
import socket

# Get the hostname
hostname = socket.gethostname()

# Get the IP address of the hostname
ip_address = socket.gethostbyname(hostname)

# Print the IP address
print("Current IP address:", ip_address)
import pandas as pd
from datetime import datetime
from flask import Flask, render_template, request, send_file
from psutil import CONN_ESTABLISHED
from sqlalchemy import create_engine, text

app = Flask(__name__)

# Set up MySQL connection
engine = create_engine('mysql+mysqlconnector://amma:EUnYfN!&UbyZ@184.168.116.149/rcoerajas_amma')

# Set up secret key for sessions
app.secret_key = 'secret'

@app.route('/')
def index():
    # Check MySQL connection status
    try:
        with engine.connect() as conn:
            db_status = "MySQL database connected"
            conn.execute(text("SELECT 1"))
    except Exception as e:
        db_status = "MySQL database not connected"
        app.logger.error(str(e))
    return render_template('index.html', db_status=db_status)

@app.route('/download')
def download():
    # Define SQL queries
    query1 = text("SELECT (SELECT `_name` FROM `members` WHERE `_id`=a.`_mbid`) AS `_member`, (SELECT `_name` FROM `districts` WHERE `_id`=a.`_district`) AS 'district', (SELECT `_name` FROM `blocks` WHERE `_id`=a.`_block`) AS 'block', (SELECT `_name` FROM `sectors` WHERE `_id`=a.`_sector`) AS 'sector', a.* FROM `ssfd` AS a")
    query2 = text("SELECT (SELECT `_name` FROM `members` WHERE `_id`=a.`_mbid`) AS `_member`, (SELECT `_name` FROM `districts` WHERE `_id`=a.`_district`) AS 'district', (SELECT `_name` FROM `blocks` WHERE `_id`=a.`_block`) AS 'block', (SELECT `_name` FROM `sectors` WHERE `_id`=a.`_sector`) AS 'sector', (SELECT `_name` FROM `panchayats` WHERE `_id`=a.`_panchayat`) AS 'panchayat', (SELECT `_name` FROM `awc` WHERE `_id`=a.`_awc`) AS 'awc',  a.* FROM `llfd` AS a")
    query3 = text("SELECT (SELECT `_malnutrition_kids_id` FROM `llfd` WHERE `_id`=a.`_llfdid`) AS 'malnutrition_id', a.* FROM `mchn` AS a")

    # Load query results into Pandas DataFrames
    try:
        with engine.connect() as conn:
            df1 = pd.read_sql(query1, conn)
            df2 = pd.read_sql(query2, conn)
            df3 = pd.read_sql(query3, conn)
    except Exception as e:
        app.logger.error(str(e))
        return render_template('error.html', error=str(e))

    # Drop unwanted columns
    df1 = df1.drop(['_id', '_mbid', '_district', '_block'], axis=1)
    df2 = df2.drop(['_id','_mbid','_district','_block','_sector','_panchayat','_awc'], axis=1)
    df3 = df3.drop(['_id','_llfdid'], axis=1)

    # Replace values in columns

    df3['_presence_on_mchn_day'] = df3['_presence_on_mchn_day'].replace({1: 'No', 0: 'Yes'})
    df3['_hunger_test'] = df3['_hunger_test'].replace({1: 'Yes'})
    df3['_current_status_after_test'] = df3['_current_status_after_test'].replace({
            1: 'बच्चे को नामांकित किया',
            2: 'उपचार चलेगा',
            0: 'NA',
            3: 'बच्चा स्वस्थ मापदंड प्राप्त कर चुका है पर एक महीने ओर उपचार चलेगा',
            4: 'उपचार हो गया और अब डिस्चार्ज किया जाएगा',
            5: 'डिफ़ाल्टर हो गया',
            6: 'MTC / उच्च स्वास्थ्य केंद्र रेफर किया गया',
            7: 'MTC/ उच्च स्वास्थ्य केंद्र से वापस लोटे बच्चे अभी भी SAM है',
            8: 'फॉलो अप चल रहा है'})
    df3['_amoxicillin_or_albendazole'] = df3['_amoxicillin_or_albendazole'].replace({
            1: 'Both',
            2: 'Only Amoxycillin',
            3: 'Only Albendazole',
            4: 'Not Applicable',
            0: 'Nothing'})
    df3['_presence_on_mchn_day'] = df3['_presence_on_mchn_day'].replace({1: 'उपस्थित', 0: 'अनुपस्थित'})

    # Save updated DataFrame to Excel file
    now = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    filename = f"data_{now}.xlsx"
    with pd.ExcelWriter(filename) as writer:
        df1.to_excel(writer, sheet_name='ssfd', index=False)
        df2.to_excel(writer, sheet_name='llfd', index=False)
        df3.to_excel(writer, sheet_name='mchn', index=False)

    # Return Excel file for download
    return send_file(filename, as_attachment=True)
if __name__=='__main__':
  app.run(host='0.0.0.0', debug=True)