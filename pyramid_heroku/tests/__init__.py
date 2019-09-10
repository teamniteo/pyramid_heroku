import unittest

from .test_herokuapp_access import TestHerokuappAccessTween
from .test_migrate import TestHerokuMigrate
from .test_request_id import TestRequestIDLogger
from .test_utils import test_expandvars_dict, test_safe_eval

if __name__ == "__main__":
    unittest.main()
