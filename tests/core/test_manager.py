"""
Test cases for logify.core.manager module
"""

import pytest
import threading
from logify.core.manager import LoggerManager, get_logger


@pytest.fixture(autouse=True)
def reset_manager():
    """Reset LoggerManager singleton before and after each test"""
    LoggerManager.reset()
    yield
    LoggerManager.reset()


class TestLoggerManagerSingleton:
    """Test LoggerManager singleton pattern"""

    def test_singleton_returns_same_instance(self):
        """Test that LoggerManager always returns the same instance"""
        manager1 = LoggerManager()
        manager2 = LoggerManager()
        assert manager1 is manager2

    def test_singleton_after_reset(self):
        """Test that reset creates a new instance"""
        manager1 = LoggerManager()
        LoggerManager.reset()
        manager2 = LoggerManager()
        # After reset, should still be singleton but fresh instance
        assert manager2 is LoggerManager()

    def test_singleton_thread_safety(self):
        """Test that singleton is thread-safe"""
        instances = []
        errors = []

        def get_instance():
            try:
                instances.append(LoggerManager())
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=get_instance) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(instances) == 10
        # All instances should be the same object
        assert all(inst is instances[0] for inst in instances)


class TestGetLogger:
    """Test LoggerManager.get_logger() method"""

    def test_get_root_logger(self):
        """Test getting the root logger"""
        manager = LoggerManager()
        logger = manager.get_logger("root")
        assert logger is not None
        assert logger.name == "root"

    def test_get_root_logger_default(self):
        """Test that default name is 'root'"""
        manager = LoggerManager()
        logger = manager.get_logger()
        assert logger.name == "root"

    def test_get_named_logger(self):
        """Test getting a named logger"""
        manager = LoggerManager()
        logger = manager.get_logger("myapp")
        assert logger is not None
        assert logger.name == "myapp"

    def test_get_hierarchical_logger(self):
        """Test getting a hierarchical logger (dot-separated name)"""
        manager = LoggerManager()
        logger = manager.get_logger("myapp.module.component")
        assert logger is not None
        assert logger.name == "myapp.module.component"

    def test_logger_caching(self):
        """Test that same logger instance is returned for same name"""
        manager = LoggerManager()
        logger1 = manager.get_logger("myapp")
        logger2 = manager.get_logger("myapp")
        assert logger1 is logger2

    def test_different_loggers_for_different_names(self):
        """Test that different names return different logger instances"""
        manager = LoggerManager()
        logger1 = manager.get_logger("app1")
        logger2 = manager.get_logger("app2")
        assert logger1 is not logger2


class TestLoggerHierarchy:
    """Test Logger hierarchy (parent-child relationships)"""

    def test_root_logger_has_no_parent(self):
        """Test that root logger has no parent"""
        manager = LoggerManager()
        root = manager.get_logger("root")
        assert root.parent is None

    def test_top_level_logger_parent_is_root(self):
        """Test that top-level logger's parent is root"""
        manager = LoggerManager()
        logger = manager.get_logger("myapp")
        root = manager.get_logger("root")
        assert logger.parent is root

    def test_nested_logger_parent_chain(self):
        """Test parent chain for nested loggers"""
        manager = LoggerManager()
        logger = manager.get_logger("app.module.component")
        
        # component's parent should be module
        assert logger.parent.name == "app.module"
        # module's parent should be app
        assert logger.parent.parent.name == "app"
        # app's parent should be root
        assert logger.parent.parent.parent.name == "root"
        # root has no parent
        assert logger.parent.parent.parent.parent is None

    def test_intermediate_loggers_created(self):
        """Test that intermediate loggers are created automatically"""
        manager = LoggerManager()
        manager.get_logger("a.b.c")
        
        all_loggers = manager.get_all_loggers()
        assert "a.b.c" in all_loggers
        assert "a.b" in all_loggers
        assert "a" in all_loggers
        assert "root" in all_loggers


class TestGetParentName:
    """Test LoggerManager._get_parent_name() method"""

    def test_simple_name_parent_is_root(self):
        """Test that simple name's parent is root"""
        manager = LoggerManager()
        assert manager._get_parent_name("myapp") == "root"

    def test_two_level_name(self):
        """Test parent name for two-level hierarchical name"""
        manager = LoggerManager()
        assert manager._get_parent_name("app.module") == "app"

    def test_three_level_name(self):
        """Test parent name for three-level hierarchical name"""
        manager = LoggerManager()
        assert manager._get_parent_name("app.module.component") == "app.module"

    def test_deep_hierarchy(self):
        """Test parent name for deeply nested name"""
        manager = LoggerManager()
        assert manager._get_parent_name("a.b.c.d.e") == "a.b.c.d"


class TestRootProperty:
    """Test LoggerManager.root property"""

    def test_root_property_returns_root_logger(self):
        """Test that root property returns the root logger"""
        manager = LoggerManager()
        root = manager.root
        assert root.name == "root"

    def test_root_property_same_as_get_logger_root(self):
        """Test that root property returns same instance as get_logger('root')"""
        manager = LoggerManager()
        root1 = manager.root
        root2 = manager.get_logger("root")
        assert root1 is root2


class TestGetAllLoggers:
    """Test LoggerManager.get_all_loggers() method"""

    def test_empty_initially(self):
        """Test that no loggers exist initially"""
        manager = LoggerManager()
        # Before any logger is created
        assert len(manager.get_all_loggers()) == 0

    def test_returns_created_loggers(self):
        """Test that get_all_loggers returns all created loggers"""
        manager = LoggerManager()
        manager.get_logger("app1")
        manager.get_logger("app2")
        manager.get_logger("app3")
        
        all_loggers = manager.get_all_loggers()
        assert "app1" in all_loggers
        assert "app2" in all_loggers
        assert "app3" in all_loggers
        assert "root" in all_loggers  # root is created as parent

    def test_returns_copy(self):
        """Test that get_all_loggers returns a copy, not the internal dict"""
        manager = LoggerManager()
        manager.get_logger("app")
        
        all_loggers = manager.get_all_loggers()
        all_loggers["fake"] = None  # Modify the returned dict
        
        # Internal dict should not be affected
        assert "fake" not in manager.get_all_loggers()


class TestClear:
    """Test LoggerManager.clear() method"""

    def test_clear_removes_all_loggers(self):
        """Test that clear removes all cached loggers"""
        manager = LoggerManager()
        manager.get_logger("app1")
        manager.get_logger("app2")
        
        manager.clear()
        
        assert len(manager.get_all_loggers()) == 0

    def test_clear_resets_root_logger(self):
        """Test that clear resets the root logger reference"""
        manager = LoggerManager()
        manager.get_logger("root")
        
        manager.clear()
        
        assert manager._root_logger is None


class TestReset:
    """Test LoggerManager.reset() class method"""

    def test_reset_clears_singleton(self):
        """Test that reset clears the singleton instance"""
        manager1 = LoggerManager()
        manager1.get_logger("app")
        
        LoggerManager.reset()
        
        manager2 = LoggerManager()
        # New manager should have no loggers
        assert len(manager2.get_all_loggers()) == 0


class TestConvenienceGetLogger:
    """Test module-level get_logger() convenience function"""

    def test_get_logger_function(self):
        """Test that get_logger function works"""
        logger = get_logger("myapp")
        assert logger is not None
        assert logger.name == "myapp"

    def test_get_logger_default_root(self):
        """Test that get_logger defaults to root"""
        logger = get_logger()
        assert logger.name == "root"

    def test_get_logger_returns_cached(self):
        """Test that get_logger returns cached instances"""
        logger1 = get_logger("myapp")
        logger2 = get_logger("myapp")
        assert logger1 is logger2


class TestThreadSafety:
    """Test thread safety of LoggerManager operations"""

    def test_concurrent_get_logger(self):
        """Test that concurrent get_logger calls are thread-safe"""
        manager = LoggerManager()
        loggers = []
        lock = threading.Lock()

        def get_and_store(name):
            logger = manager.get_logger(name)
            with lock:
                loggers.append((name, logger))

        # Create multiple threads requesting same and different loggers
        threads = []
        for i in range(5):
            threads.append(threading.Thread(target=get_and_store, args=("shared",)))
            threads.append(threading.Thread(target=get_and_store, args=(f"unique_{i}",)))

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All "shared" loggers should be the same instance
        shared_loggers = [l for name, l in loggers if name == "shared"]
        assert len(shared_loggers) == 5
        assert all(l is shared_loggers[0] for l in shared_loggers)

        # Unique loggers should be different
        unique_loggers = [l for name, l in loggers if name.startswith("unique_")]
        assert len(unique_loggers) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
