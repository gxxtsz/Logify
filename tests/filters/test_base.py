"""
Test cases for logify.filters.base module
"""

import pytest
from logify.filters.base import BaseFilter, FilterChain
from logify.core.record import LogRecord
from logify.core.levels import INFO, DEBUG, WARNING, ERROR


class ConcreteFilter(BaseFilter):
    """Concrete implementation of BaseFilter for testing"""
    
    def __init__(self, should_pass: bool = True, name: str = ""):
        super().__init__(name)
        self.should_pass = should_pass
        self.filter_called = False
    
    def filter(self, record: LogRecord) -> bool:
        self.filter_called = True
        return self.should_pass


class TestBaseFilter:
    """Test BaseFilter abstract class"""

    def test_default_name_is_class_name(self):
        """Test that default name is the class name"""
        filter_ = ConcreteFilter()
        assert filter_.name == "ConcreteFilter"

    def test_custom_name(self):
        """Test providing a custom name"""
        filter_ = ConcreteFilter(name="MyFilter")
        assert filter_.name == "MyFilter"

    def test_empty_name_uses_class_name(self):
        """Test that empty string name uses class name"""
        filter_ = ConcreteFilter(name="")
        assert filter_.name == "ConcreteFilter"

    def test_repr(self):
        """Test __repr__ method"""
        filter_ = ConcreteFilter(name="TestFilter")
        repr_str = repr(filter_)
        assert "ConcreteFilter" in repr_str
        assert "TestFilter" in repr_str

    def test_filter_method_called(self):
        """Test that filter method is called"""
        filter_ = ConcreteFilter()
        record = LogRecord(name="test", level=INFO, msg="Test message")
        
        filter_.filter(record)
        
        assert filter_.filter_called is True

    def test_filter_returns_true(self):
        """Test filter returning True"""
        filter_ = ConcreteFilter(should_pass=True)
        record = LogRecord(name="test", level=INFO, msg="Test message")
        
        result = filter_.filter(record)
        
        assert result is True

    def test_filter_returns_false(self):
        """Test filter returning False"""
        filter_ = ConcreteFilter(should_pass=False)
        record = LogRecord(name="test", level=INFO, msg="Test message")
        
        result = filter_.filter(record)
        
        assert result is False


class TestFilterChain:
    """Test FilterChain class"""

    def test_empty_chain_init(self):
        """Test creating an empty filter chain"""
        chain = FilterChain()
        assert len(chain) == 0

    def test_add_filter(self):
        """Test adding a filter to the chain"""
        chain = FilterChain()
        filter_ = ConcreteFilter()
        
        chain.add_filter(filter_)
        
        assert len(chain) == 1
        assert filter_ in chain.filters

    def test_add_filter_returns_self(self):
        """Test that add_filter returns self for chaining"""
        chain = FilterChain()
        filter_ = ConcreteFilter()
        
        result = chain.add_filter(filter_)
        
        assert result is chain

    def test_add_filter_chaining(self):
        """Test chaining multiple add_filter calls"""
        chain = FilterChain()
        filter1 = ConcreteFilter(name="f1")
        filter2 = ConcreteFilter(name="f2")
        filter3 = ConcreteFilter(name="f3")
        
        chain.add_filter(filter1).add_filter(filter2).add_filter(filter3)
        
        assert len(chain) == 3

    def test_add_duplicate_filter_ignored(self):
        """Test that adding the same filter twice is ignored"""
        chain = FilterChain()
        filter_ = ConcreteFilter()
        
        chain.add_filter(filter_)
        chain.add_filter(filter_)
        
        assert len(chain) == 1

    def test_remove_filter(self):
        """Test removing a filter from the chain"""
        chain = FilterChain()
        filter_ = ConcreteFilter()
        chain.add_filter(filter_)
        
        chain.remove_filter(filter_)
        
        assert len(chain) == 0
        assert filter_ not in chain.filters

    def test_remove_filter_returns_self(self):
        """Test that remove_filter returns self for chaining"""
        chain = FilterChain()
        filter_ = ConcreteFilter()
        chain.add_filter(filter_)
        
        result = chain.remove_filter(filter_)
        
        assert result is chain

    def test_remove_nonexistent_filter(self):
        """Test removing a filter that's not in the chain"""
        chain = FilterChain()
        filter_ = ConcreteFilter()
        
        # Should not raise an error
        chain.remove_filter(filter_)
        
        assert len(chain) == 0

    def test_filter_empty_chain_passes(self):
        """Test that empty chain passes all records"""
        chain = FilterChain()
        record = LogRecord(name="test", level=INFO, msg="Test message")
        
        result = chain.filter(record)
        
        assert result is True

    def test_filter_all_pass(self):
        """Test chain passes when all filters pass"""
        chain = FilterChain()
        chain.add_filter(ConcreteFilter(should_pass=True))
        chain.add_filter(ConcreteFilter(should_pass=True))
        chain.add_filter(ConcreteFilter(should_pass=True))
        
        record = LogRecord(name="test", level=INFO, msg="Test message")
        result = chain.filter(record)
        
        assert result is True

    def test_filter_one_fails(self):
        """Test chain fails when one filter fails"""
        chain = FilterChain()
        chain.add_filter(ConcreteFilter(should_pass=True))
        chain.add_filter(ConcreteFilter(should_pass=False))
        chain.add_filter(ConcreteFilter(should_pass=True))
        
        record = LogRecord(name="test", level=INFO, msg="Test message")
        result = chain.filter(record)
        
        assert result is False

    def test_filter_first_fails_short_circuits(self):
        """Test that chain short-circuits when first filter fails"""
        chain = FilterChain()
        filter1 = ConcreteFilter(should_pass=False)
        filter2 = ConcreteFilter(should_pass=True)
        chain.add_filter(filter1)
        chain.add_filter(filter2)
        
        record = LogRecord(name="test", level=INFO, msg="Test message")
        chain.filter(record)
        
        assert filter1.filter_called is True
        assert filter2.filter_called is False  # Short-circuited

    def test_clear(self):
        """Test clearing all filters from chain"""
        chain = FilterChain()
        chain.add_filter(ConcreteFilter())
        chain.add_filter(ConcreteFilter())
        chain.add_filter(ConcreteFilter())
        
        chain.clear()
        
        assert len(chain) == 0

    def test_filters_property_returns_copy(self):
        """Test that filters property returns a copy"""
        chain = FilterChain()
        filter_ = ConcreteFilter()
        chain.add_filter(filter_)
        
        filters = chain.filters
        filters.append(ConcreteFilter())
        
        assert len(chain) == 1  # Original not affected

    def test_len(self):
        """Test __len__ method"""
        chain = FilterChain()
        assert len(chain) == 0
        
        chain.add_filter(ConcreteFilter())
        assert len(chain) == 1
        
        chain.add_filter(ConcreteFilter())
        assert len(chain) == 2

    def test_repr(self):
        """Test __repr__ method"""
        chain = FilterChain()
        chain.add_filter(ConcreteFilter())
        chain.add_filter(ConcreteFilter())
        
        repr_str = repr(chain)
        
        assert "FilterChain" in repr_str
        assert "2" in repr_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
