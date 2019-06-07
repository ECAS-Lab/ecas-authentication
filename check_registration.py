import sys
import configparser
import mysql.connector
from mysql.connector import errorcode

def main(username,email):
	
	try:
	
		config = configparser.ConfigParser()
		config.read('config.ini')
		user=config['ophidia']['user']
		pwd=config['ophidia']['pass']
		host=config['ophidia']['host']
		db=config['ophidia']['db']
		con = mysql.connector.connect(user=user, password=pwd,host=host,database=db)
		c = con.cursor()
		c.execute("""SELECT * FROM user""")
		result_set = c.fetchall()
		for row in result_set:
			if username == row[4] and email == row[3]:
				return True	
		con.close()
		return False

	except mysql.connector.Error as err:
		print(err)
