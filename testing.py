__author__ = 'AivanF'
__copyright__ = 'Copyright 2020, AivanF'
__contact__ = 'projects@aivanf.com'

import unittest
from tests.test_column import TestLemurasColumns
from tests.test_row import TestLemurasRows
from tests.test_table import TestLemurasTable
from tests.test_table_pivot import TestLemurasTablePivot 
from tests.test_table_concat import TestLemurasTableConcat
from tests.test_table_groupby import TestLemurasTableGroupby
from tests.test_table_merge import TestLemurasTableMerge
from tests.test_format_csv import TestLemurasCsv
from tests.test_format_json import TestLemurasJson
from tests.test_format_html import TestLemurasHtml
from tests.test_format_sql import TestLemurasSql

if __name__ == '__main__':
	import sys
	print('Python version:\n{}\n{}\nStarting Lemuras unit tests'.format(sys.version, '-'*70))
	unittest.main()
