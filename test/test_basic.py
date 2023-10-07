import os

import pymysql
import requests
import unittest
import yaml

from pymyelarepl import PyMyElaRepl


class BasicTestCase(unittest.TestCase):
    def execute(self, query):
        cursor = self.conn_control.cursor()
        cursor.execute(query)
        return cursor

    def setUp(self):
        config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')

        with open(config_path) as f:
            self.config = yaml.load(f, Loader=yaml.FullLoader)

        mysql_config = {
            "host": self.config['mysql']['host'],
            "user": self.config['mysql']['user'],
            "passwd": self.config['mysql']['password'],
            "port": self.config['mysql']['port'],
            "use_unicode": True,
            "charset": "utf8", # regarded as utf8mb4
        }

        self.conn_control = pymysql.connect(**mysql_config)
        self.execute("DROP DATABASE IF EXISTS {db}".format(db=self.config['mysql']['db']))
        self.execute("CREATE DATABASE {db}".format(db=self.config['mysql']['db']))
        self.execute("USE {db}".format(db=self.config['mysql']['db']))
        self.execute("RESET MASTER")

        self.es_url_for_all_data = 'http://{host}:{port}/_all'.format( 
            host=self.config['es']['host'],
            port=self.config['es']['port']
        )  

        self.pymyelarepl = PyMyElaRepl(config_path)

    def test_basic_replication(self):
        self.execute(
            """
		    CREATE TABLE basic_replication( 
		    id INT PRIMARY KEY AUTO_INCREMENT, 
		    f FLOAT, 
		    t TIMESTAMP)
            """
        )
        
        self.execute("INSERT INTO basic_replication(id, f, t) VALUES(1, 12.34, '2023-09-25 00:00:00')")
        self.execute("INSERT INTO basic_replication(id, f, t) VALUES(2, 12.34, '2023-09-25 00:00:00')")
        self.conn_control.commit()

        self.execute("UPDATE basic_replication SET f=56.78 WHERE id=1")
        self.execute("UPDATE basic_replication SET f=56.78 WHERE id=2")
        self.conn_control.commit()

        self.execute("DELETE FROM basic_replication WHERE id=1")
        self.execute("DELETE FROM basic_replication WHERE id=2")
        self.conn_control.commit()
        
        self.pymyelarepl.run()
        if_error = True if True in self.pymyelarepl.if_error else False
        self.assertEqual(if_error, False)

    def tearDown(self):
        self.execute("DROP DATABASE IF EXISTS {db}".format(db=self.config['mysql']['db']))
        self.execute("RESET MASTER")
        self.conn_control.close()
        requests.delete(self.es_url_for_all_data)

unittest.main()