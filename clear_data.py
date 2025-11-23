#!/usr/bin/env python
import sqlite3

DB_PATH = 'palus_vikas.db'

def clear_all_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Delete all complaints
    cursor.execute('DELETE FROM complaints')
    complaints_deleted = cursor.rowcount
    print(f'Deleted {complaints_deleted} complaints')
    
    # Delete all scheme applications
    cursor.execute('DELETE FROM scheme_applications')
    scheme_deleted = cursor.rowcount
    print(f'Deleted {scheme_deleted} scheme applications')
    
    conn.commit()
    conn.close()
    
    print('\n✓ All data deleted permanently from database')

if __name__ == '__main__':
    clear_all_data()
