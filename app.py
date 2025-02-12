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



