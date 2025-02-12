from flask import Flask, render_template
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import pandas as pd

app = Flask(__name__)
load_dotenv()

# Database connection details
db_host = os.getenv('DB_HOST')
db_user = os.getenv('DB_USER')
db_pass = os.getenv('DB_PASSWORD')
db_name = os.getenv('DB_NAME')

DATABASE_URL = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}/{db_name}"
engine = create_engine(DATABASE_URL)


@app.route('/')
def index():
    new_all_suplayer = new_group_data(table='vervotech_hotel_map_new', engine=engine)
    
    update_all_suplayer = new_group_data(table='vervotech_hotel_map_update', engine=engine)

    merged_data = pd.merge(new_all_suplayer, update_all_suplayer, on='ProviderFamily', how='outer', suffixes=('_new', '_update'))

    merged_data.fillna(0, inplace=True)

    merged_data = merged_data.astype({'value_count_new': 'int', 'value_count_update': 'int'})

    group_data = merged_data.to_dict(orient='records')

    latest_record = fetch_latest_record(engine)
    latest_record['vh_new_newFile_updateSuccess'] = int(latest_record['vh_new_newFile_updateSuccess'])
    latest_record['vh_new_newFile_updateSkipping'] = int(latest_record['vh_new_newFile_updateSkipping'])
    latest_record['vh_update_newFile_updateSuccess'] = int(latest_record['vh_update_newFile_updateSuccess'])
    latest_record['vh_update_newFile_updateSkipping'] = int(latest_record['vh_update_newFile_updateSkipping'])
    latest_record['vh_mapping_newFile'] = int(latest_record['vh_mapping_newFile'])

    live_updates = live_data_uploading_function(table='vervotech_mapping', engine=engine)

    # Render the template with the merged group data
    return render_template('index.html', latest_record=latest_record, live_updates=live_updates, group_data=group_data)



@app.route('/live_updates')
def live_updates_route():
    live_updates = live_data_uploading_function(table='vervotech_mapping', engine=engine)
    return {
        'count': live_updates['count'],
        'last_update': live_updates['last_update']
    }

def fetch_latest_record(engine):
    try:
        query = text("SELECT * FROM vervotech_update_data_info ORDER BY created_at DESC LIMIT 1;")
        
        with engine.connect() as connection:
            result = connection.execute(query)
            latest_record = result.fetchone()  
            
            if latest_record is not None:
                record_dict = {
                    'Id': latest_record[0],
                    'vh_new_total': latest_record[1],
                    'vh_new_newFile': latest_record[2],
                    'vh_new_newFile_updateSuccess': latest_record[3],
                    'vh_new_newFile_updateSkipping': latest_record[4],
                    'vh_new_newFile_lastUpdate_dateTime': latest_record[5],
                    'vh_update_total': latest_record[6],
                    'vh_update_newFile': latest_record[7],
                    'vh_update_newFile_updateSuccess': latest_record[8],
                    'vh_update_newFile_updateSkipping': latest_record[9],
                    'vh_update_newFile_lastUpdate_dateTime': latest_record[10],
                    'vh_mapping_total': latest_record[11],
                    'vh_mapping_newFile': latest_record[12],
                    'created_at': latest_record[13],
                    'ModifiedOn': latest_record[14],
                    'contentUpdatingStatus': latest_record[15],
                    'Agoda_newData': latest_record[16],
                    'Agoda_updateData': latest_record[17],
                    'Hotelbeds_newData': latest_record[18],
                    'Hotelbeds_updateData': latest_record[19]
                }

                return record_dict
            else:
                return None
    except Exception as e:
        print(f"An error occurred while fetching the latest record: {e}")
        return None




def new_group_data(table, engine):
    query = f"""
    SELECT ProviderFamily, COUNT(*) AS value_count
    FROM {table}
    WHERE DATE(created_at) = (
        SELECT DATE(MAX(created_at)) 
        FROM {table}
    )
    GROUP BY ProviderFamily;
    """
    df = pd.read_sql(query, engine)
    return df  



if __name__ == '__main__':
    app.run(debug=True, port=2424)
