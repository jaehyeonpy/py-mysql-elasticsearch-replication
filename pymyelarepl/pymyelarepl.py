import datetime
import decimal
import json

import requests
import yaml

from pymysqlreplication import BinLogStreamReader
from pymysqlreplication.row_event import DeleteRowsEvent, UpdateRowsEvent, WriteRowsEvent


class PyMyElaRepl:
    def get_config_from_file(self, config_path):
        try:
            with open(config_path) as f:
                self.config = yaml.load(f, Loader=yaml.FullLoader)
        except IndexError:
            raise IndexError('Must specify config file')
        except FileNotFoundError:
            raise FileNotFoundError('Could not find the config file')

    def __init__(self, config_path):
        self.get_config_from_file(config_path)

        self.es_endpoint = 'http://{host}:{port}/_bulk'.format( 
            host=self.config['es']['host'],
            port=self.config['es']['port']
        )  

        self.mysql_conf = dict(
            [(key, self.config['mysql'][key]) for key in ['host', 'port', 'user', 'password']]
        )

        self.binlog_stream_reader = BinLogStreamReader(
            connection_settings=self.mysql_conf,
            server_id=self.config['mysql']['server_id'],
            only_events=[DeleteRowsEvent, WriteRowsEvent, UpdateRowsEvent],
            log_file=self.config['mysql']['log_file'],
            log_pos=self.config['mysql']['log_pos'],
            resume_stream=True if self.config['mysql']['log_pos'] != 0 else False, 
            blocking=self.config['mysql']['blocking']
        )

        self.if_error = []

    def send_to_es(self, converted):        
        resp = requests.post(
            url=self.es_endpoint, 
            data=converted, 
            verify=False,
            headers={'content-type': 'application/json'}
        )

        self.if_error.append(resp.json()['errors'])
        print(resp.json())

    def serialize_not_serializable(self, obj): 
        if isinstance(obj, datetime.datetime) or isinstance(obj, datetime.date):
            return obj.isoformat()
        elif isinstance(obj, decimal.Decimal):
            return str(obj)
        raise TypeError('Type not serializable for obj {obj}'.format(obj=obj))
    
    def convert_event_to_valid_es_data_format(self, event): 
        meta = json.dumps({event['action']: {'_index': event['index'], '_id': event['id']}})
            
        if event['action'] == 'delete':
            converted = meta + '\n'
        elif event['action'] == 'update':
            body = json.dumps({'doc': event['doc']}, default=self.serialize_not_serializable)
            converted = meta + '\n' + body + '\n'
        elif event['action'] == 'create':
            body = json.dumps(event['doc'], default=self.serialize_not_serializable)
            converted = meta + '\n' + body + '\n'
        
        return converted

    def get_binlog_event(self):        
        for event in self.binlog_stream_reader:
            for row in event.rows: 
                if isinstance(event, DeleteRowsEvent):
                    extracted = {
                        'index': event.table,
                        'id': row['values'][event.primary_key],
                        'action': 'delete'
                    }
                elif isinstance(event, UpdateRowsEvent):
                    extracted = {
                        'index': event.table,
                        'id': row['after_values'][event.primary_key],
                        'action': 'update',
                        'doc': {k: v for k, v in row['after_values'].items() if k != event.primary_key}
                    }
                elif isinstance(event, WriteRowsEvent):
                    extracted = {
                        'index': event.table,
                        'id': row['values'][event.primary_key],
                        'action': 'create',
                        'doc': {k: v for k, v in row['values'].items() if k != event.primary_key}
                    }

                yield extracted

        self.binlog_stream_reader.close()
        print('Info: Mysql connection closed successfully after reading all binlog events.')
    
    def run(self):
        for event in self.get_binlog_event():
            converted = self.convert_event_to_valid_es_data_format(event)
            self.send_to_es(converted)