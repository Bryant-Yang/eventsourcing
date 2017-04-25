import time
from unittest.case import TestCase
from uuid import uuid1

from eventsourcing.utils.time import timestamp_from_uuid


class TestUtils(TestCase):
    def test_timestamp_from_uuid(self):
        until = time.time()
        uuid = uuid1()
        after = time.time()
        uuid_timestamp = timestamp_from_uuid(uuid)
        self.assertLess(until, uuid_timestamp)
        self.assertGreater(after, uuid_timestamp)

        # Check timestamp_from_uuid() works with hex strings, as well as UUID objects.
        self.assertEqual(timestamp_from_uuid(uuid.hex), timestamp_from_uuid(uuid))
