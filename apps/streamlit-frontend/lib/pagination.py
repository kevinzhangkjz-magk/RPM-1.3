"""
Pagination utilities for efficient data loading
Implements server-side pagination for large datasets
"""

import streamlit as st
from typing import Any, Dict, List, Optional, Tuple, Callable
import math
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class PaginationConfig:
    """Configuration for pagination."""
    page_size: int = 25
    max_page_size: int = 100
    show_page_size_selector: bool = True
    show_total_count: bool = True
    show_page_jumper: bool = True
    available_page_sizes: List[int] = None
    
    def __post_init__(self):
        if self.available_page_sizes is None:
            self.available_page_sizes = [10, 25, 50, 100]


class DataPaginator:
    """
    Handles pagination for large datasets with server-side support.
    """
    
    def __init__(self, 
                 data_fetcher: Callable,
                 config: Optional[PaginationConfig] = None,
                 cache_pages: bool = True):
        """
        Initialize paginator.
        
        Args:
            data_fetcher: Function to fetch data (should accept offset, limit params)
            config: Pagination configuration
            cache_pages: Whether to cache fetched pages
        """
        self.data_fetcher = data_fetcher
        self.config = config or PaginationConfig()
        self.cache_pages = cache_pages
        self._page_cache = {}
        self._total_count = None
    
    def get_page_data(self, 
                     page_num: int, 
                     page_size: int,
                     filters: Optional[Dict] = None) -> Tuple[List[Any], int]:
        """
        Get data for specific page.
        
        Args:
            page_num: Page number (1-indexed)
            page_size: Items per page
            filters: Optional filters to apply
            
        Returns:
            Tuple of (page_data, total_count)
        """
        # Validate inputs
        page_num = max(1, page_num)
        page_size = min(max(1, page_size), self.config.max_page_size)
        
        # Calculate offset
        offset = (page_num - 1) * page_size
        
        # Check cache if enabled
        cache_key = self._get_cache_key(page_num, page_size, filters)
        if self.cache_pages and cache_key in self._page_cache:
            logger.debug(f"Returning cached page {page_num}")
            return self._page_cache[cache_key]
        
        # Fetch data from server
        try:
            result = self.data_fetcher(
                offset=offset,
                limit=page_size,
                filters=filters
            )
            
            # Handle different response formats
            if isinstance(result, dict):
                data = result.get('data', [])
                total_count = result.get('total_count', len(data))
            elif isinstance(result, tuple):
                data, total_count = result
            else:
                data = result
                total_count = len(data)
            
            # Update total count
            self._total_count = total_count
            
            # Cache if enabled
            if self.cache_pages:
                self._page_cache[cache_key] = (data, total_count)
            
            logger.info(f"Fetched page {page_num} with {len(data)} items")
            return data, total_count
            
        except Exception as e:
            logger.error(f"Error fetching page {page_num}: {str(e)}")
            return [], 0
    
    def _get_cache_key(self, page_num: int, page_size: int, filters: Optional[Dict]) -> str:
        """Generate cache key for page."""
        filter_str = str(sorted(filters.items())) if filters else ""
        return f"{page_num}_{page_size}_{filter_str}"
    
    def clear_cache(self) -> None:
        """Clear page cache."""
        self._page_cache.clear()
        self._total_count = None
        logger.debug("Page cache cleared")
    
    def render_pagination_controls(self, 
                                  key_prefix: str = "paginator",
                                  filters: Optional[Dict] = None) -> Tuple[List[Any], Dict]:
        """
        Render pagination controls and return current page data.
        
        Args:
            key_prefix: Prefix for widget keys
            filters: Optional filters to apply
            
        Returns:
            Tuple of (current_page_data, pagination_info)
        """
        # Initialize session state for pagination
        if f"{key_prefix}_page" not in st.session_state:
            st.session_state[f"{key_prefix}_page"] = 1
        if f"{key_prefix}_page_size" not in st.session_state:
            st.session_state[f"{key_prefix}_page_size"] = self.config.page_size
        
        current_page = st.session_state[f"{key_prefix}_page"]
        page_size = st.session_state[f"{key_prefix}_page_size"]
        
        # Get data for current page
        page_data, total_count = self.get_page_data(current_page, page_size, filters)
        
        # Calculate pagination info
        total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1
        
        # Render controls
        col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
        
        with col1:
            # Previous button
            if st.button("◀ Previous", 
                        key=f"{key_prefix}_prev",
                        disabled=current_page <= 1,
                        use_container_width=True):
                st.session_state[f"{key_prefix}_page"] = current_page - 1
                st.rerun()
        
        with col2:
            # Page size selector
            if self.config.show_page_size_selector:
                new_page_size = st.selectbox(
                    "Page size",
                    self.config.available_page_sizes,
                    index=self.config.available_page_sizes.index(page_size),
                    key=f"{key_prefix}_size_select"
                )
                if new_page_size != page_size:
                    st.session_state[f"{key_prefix}_page_size"] = new_page_size
                    st.session_state[f"{key_prefix}_page"] = 1  # Reset to first page
                    st.rerun()
        
        with col3:
            # Page info and jumper
            if self.config.show_page_jumper:
                # Create columns for inline display
                jump_col1, jump_col2, jump_col3 = st.columns([1, 2, 1])
                
                with jump_col1:
                    st.markdown(f"<div style='padding-top: 8px;'>Page</div>", 
                              unsafe_allow_html=True)
                
                with jump_col2:
                    new_page = st.number_input(
                        "Jump to page",
                        min_value=1,
                        max_value=total_pages,
                        value=current_page,
                        key=f"{key_prefix}_jumper",
                        label_visibility="collapsed"
                    )
                    if new_page != current_page:
                        st.session_state[f"{key_prefix}_page"] = new_page
                        st.rerun()
                
                with jump_col3:
                    st.markdown(f"<div style='padding-top: 8px;'>of {total_pages}</div>", 
                              unsafe_allow_html=True)
            else:
                st.markdown(f"Page {current_page} of {total_pages}")
        
        with col4:
            # Total count
            if self.config.show_total_count:
                st.markdown(f"<div style='text-align: center; padding-top: 8px;'>"
                          f"Total: {total_count}</div>", 
                          unsafe_allow_html=True)
        
        with col5:
            # Next button
            if st.button("Next ▶", 
                        key=f"{key_prefix}_next",
                        disabled=current_page >= total_pages,
                        use_container_width=True):
                st.session_state[f"{key_prefix}_page"] = current_page + 1
                st.rerun()
        
        # Return data and info
        pagination_info = {
            'current_page': current_page,
            'page_size': page_size,
            'total_count': total_count,
            'total_pages': total_pages,
            'offset': (current_page - 1) * page_size,
            'has_next': current_page < total_pages,
            'has_prev': current_page > 1
        }
        
        return page_data, pagination_info


class InfiniteScroller:
    """
    Implements infinite scrolling for data loading.
    """
    
    def __init__(self, 
                 data_fetcher: Callable,
                 batch_size: int = 20,
                 threshold: float = 0.8):
        """
        Initialize infinite scroller.
        
        Args:
            data_fetcher: Function to fetch data batches
            batch_size: Items per batch
            threshold: Scroll threshold to trigger load (0-1)
        """
        self.data_fetcher = data_fetcher
        self.batch_size = batch_size
        self.threshold = threshold
        self._loaded_data = []
        self._has_more = True
        self._loading = False
    
    def render_scrollable_list(self, 
                              render_item: Callable,
                              container_height: int = 600,
                              key_prefix: str = "scroller") -> None:
        """
        Render scrollable list with infinite loading.
        
        Args:
            render_item: Function to render each item
            container_height: Container height in pixels
            key_prefix: Prefix for widget keys
        """
        # Initialize session state
        if f"{key_prefix}_offset" not in st.session_state:
            st.session_state[f"{key_prefix}_offset"] = 0
            st.session_state[f"{key_prefix}_data"] = []
            st.session_state[f"{key_prefix}_has_more"] = True
        
        # Load initial data if needed
        if not st.session_state[f"{key_prefix}_data"]:
            self._load_batch(key_prefix)
        
        # Create scrollable container
        container = st.container(height=container_height)
        
        with container:
            # Render loaded items
            for idx, item in enumerate(st.session_state[f"{key_prefix}_data"]):
                render_item(item, idx)
            
            # Load more button or indicator
            if st.session_state[f"{key_prefix}_has_more"]:
                if st.button("Load More", 
                           key=f"{key_prefix}_load_more",
                           use_container_width=True):
                    self._load_batch(key_prefix)
                    st.rerun()
            else:
                st.info("No more items to load")
    
    def _load_batch(self, key_prefix: str) -> None:
        """Load next batch of data."""
        offset = st.session_state[f"{key_prefix}_offset"]
        
        try:
            # Fetch next batch
            result = self.data_fetcher(
                offset=offset,
                limit=self.batch_size
            )
            
            # Handle response
            if isinstance(result, dict):
                new_data = result.get('data', [])
                has_more = result.get('has_more', len(new_data) == self.batch_size)
            else:
                new_data = result
                has_more = len(new_data) == self.batch_size
            
            # Update session state
            st.session_state[f"{key_prefix}_data"].extend(new_data)
            st.session_state[f"{key_prefix}_offset"] = offset + len(new_data)
            st.session_state[f"{key_prefix}_has_more"] = has_more
            
            logger.info(f"Loaded {len(new_data)} items at offset {offset}")
            
        except Exception as e:
            logger.error(f"Error loading batch at offset {offset}: {str(e)}")
            st.session_state[f"{key_prefix}_has_more"] = False


def paginate_dataframe(df: 'pd.DataFrame', 
                       page_size: int = 25,
                       key_prefix: str = "df_paginator") -> 'pd.DataFrame':
    """
    Simple pagination for pandas DataFrames.
    
    Args:
        df: DataFrame to paginate
        page_size: Rows per page
        key_prefix: Prefix for widget keys
        
    Returns:
        Paginated DataFrame slice
    """
    import pandas as pd
    
    total_rows = len(df)
    total_pages = math.ceil(total_rows / page_size)
    
    # Initialize page in session state
    if f"{key_prefix}_page" not in st.session_state:
        st.session_state[f"{key_prefix}_page"] = 1
    
    current_page = st.session_state[f"{key_prefix}_page"]
    
    # Calculate slice
    start_idx = (current_page - 1) * page_size
    end_idx = min(start_idx + page_size, total_rows)
    
    # Render controls
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("◀ Previous", 
                    key=f"{key_prefix}_prev",
                    disabled=current_page <= 1):
            st.session_state[f"{key_prefix}_page"] = current_page - 1
            st.rerun()
    
    with col2:
        st.markdown(f"<div style='text-align: center;'>"
                   f"Page {current_page} of {total_pages} "
                   f"({total_rows} total rows)</div>",
                   unsafe_allow_html=True)
    
    with col3:
        if st.button("Next ▶", 
                    key=f"{key_prefix}_next",
                    disabled=current_page >= total_pages):
            st.session_state[f"{key_prefix}_page"] = current_page + 1
            st.rerun()
    
    # Return sliced dataframe
    return df.iloc[start_idx:end_idx]


# Example usage for API data fetching
def create_api_paginator(api_client, endpoint: str) -> DataPaginator:
    """
    Create paginator for API endpoint.
    
    Args:
        api_client: API client instance
        endpoint: API endpoint
        
    Returns:
        Configured DataPaginator
    """
    def fetch_page(offset: int, limit: int, filters: Optional[Dict] = None):
        """Fetch page from API."""
        params = {
            'offset': offset,
            'limit': limit
        }
        if filters:
            params.update(filters)
        
        response = api_client._make_request('GET', endpoint, params=params)
        return response.json()
    
    return DataPaginator(
        data_fetcher=fetch_page,
        config=PaginationConfig(
            page_size=25,
            available_page_sizes=[10, 25, 50, 100]
        )
    )