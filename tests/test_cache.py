import unittest
from app.utils.cache import get_pipeline_step_config


class TestCache(unittest.TestCase):
    """Unit tests for functools.lru_cache implementation."""

    def setUp(self):
        get_pipeline_step_config.cache_clear()

    def test_repeated_calls_use_cache(self):
        # Initial call should be a cache miss
        config1 = get_pipeline_step_config("TaskValidationStep", "production")
        info1 = get_pipeline_step_config.cache_info()
        self.assertEqual(info1.hits, 0)
        self.assertEqual(info1.misses, 1)

        # Subsequent call with identical arguments should be a cache hit
        config2 = get_pipeline_step_config("TaskValidationStep", "production")
        info2 = get_pipeline_step_config.cache_info()
        self.assertEqual(info2.hits, 1)
        self.assertEqual(info2.misses, 1)

        # Results should be equal
        self.assertEqual(config1, config2)

    def test_cache_clear(self):
        get_pipeline_step_config("TaskTransformationStep", "test")
        info_before = get_pipeline_step_config.cache_info()
        self.assertGreater(info_before.currsize, 0)

        get_pipeline_step_config.cache_clear()
        info_after = get_pipeline_step_config.cache_info()
        self.assertEqual(info_after.currsize, 0)
        self.assertEqual(info_after.hits, 0)
        self.assertEqual(info_after.misses, 0)

    def test_deterministic_behavior(self):
        cfg_val = get_pipeline_step_config("TaskValidationStep")
        cfg_proc = get_pipeline_step_config("TaskProcessingStep")

        self.assertTrue(cfg_val["title_required"])
        self.assertEqual(cfg_proc["status_label"], "PROCESSED")


if __name__ == "__main__":
    unittest.main()
