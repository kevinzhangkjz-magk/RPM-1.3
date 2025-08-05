"""
Navigation components for Streamlit application
Includes breadcrumb navigation and hierarchical drill-down
"""

import streamlit as st
from typing import Optional, List, Dict


def render_breadcrumb() -> None:
    """
    Render breadcrumb navigation based on current context.
    Shows: Home > Portfolio > Site > Skid > Inverter
    """
    breadcrumb_parts = ["🏠 Home"]
    
    # Build breadcrumb based on session state
    if st.session_state.get('selected_site'):
        breadcrumb_parts.append(f"📊 Site: {st.session_state.selected_site}")
    
    if st.session_state.get('selected_skid'):
        breadcrumb_parts.append(f"⚙️ Skid: {st.session_state.selected_skid}")
    
    if st.session_state.get('selected_inverter'):
        breadcrumb_parts.append(f"🔌 Inverter: {st.session_state.selected_inverter}")
    
    # Render breadcrumb
    breadcrumb_html = " > ".join(breadcrumb_parts)
    st.markdown(f"**Navigation:** {breadcrumb_html}")


def render_site_selector(sites: List[Dict]) -> Optional[str]:
    """
    Render site selection dropdown.
    
    Args:
        sites: List of site dictionaries
        
    Returns:
        Selected site ID or None
    """
    if not sites:
        st.warning("No sites available")
        return None
    
    # Create options for selectbox
    site_options = {
        f"{site.get('site_name', site['site_id'])} ({site['site_id']})": site['site_id']
        for site in sites
    }
    
    # Add empty option
    options = ["Select a site..."] + list(site_options.keys())
    
    selected = st.selectbox(
        "Select Site",
        options,
        index=0,
        key="site_selector"
    )
    
    if selected != "Select a site...":
        return site_options[selected]
    
    return None


def render_skid_selector(skids: List[Dict]) -> Optional[str]:
    """
    Render skid selection dropdown.
    
    Args:
        skids: List of skid dictionaries
        
    Returns:
        Selected skid ID or None
    """
    if not skids:
        st.info("No skids available for this site")
        return None
    
    # Create options for selectbox
    skid_options = {
        f"Skid {skid['skid_id']}": skid['skid_id']
        for skid in skids
    }
    
    # Add options
    options = ["All Skids"] + list(skid_options.keys())
    
    selected = st.selectbox(
        "Select Skid",
        options,
        index=0,
        key="skid_selector"
    )
    
    if selected != "All Skids":
        return skid_options[selected]
    
    return None


def render_inverter_selector(inverters: List[Dict]) -> Optional[str]:
    """
    Render inverter selection dropdown.
    
    Args:
        inverters: List of inverter dictionaries
        
    Returns:
        Selected inverter ID or None
    """
    if not inverters:
        st.info("No inverters available")
        return None
    
    # Create options for selectbox
    inverter_options = {
        f"Inverter {inv['inverter_id']}": inv['inverter_id']
        for inv in inverters
    }
    
    # Add options
    options = ["All Inverters"] + list(inverter_options.keys())
    
    selected = st.selectbox(
        "Select Inverter",
        options,
        index=0,
        key="inverter_selector"
    )
    
    if selected != "All Inverters":
        return inverter_options[selected]
    
    return None


def render_hierarchical_navigation(api_client) -> Dict:
    """
    Render complete hierarchical navigation interface.
    
    Args:
        api_client: API client instance
        
    Returns:
        Dictionary with selected site, skid, and inverter IDs
    """
    navigation_state = {
        'site_id': None,
        'skid_id': None,
        'inverter_id': None
    }
    
    # Site selection
    sites = api_client.get_sites()
    selected_site = render_site_selector(sites)
    
    if selected_site:
        navigation_state['site_id'] = selected_site
        st.session_state.selected_site = selected_site
        
        # Skid selection
        skids = api_client.get_site_skids(selected_site)
        selected_skid = render_skid_selector(skids)
        
        if selected_skid:
            navigation_state['skid_id'] = selected_skid
            st.session_state.selected_skid = selected_skid
            
            # Inverter selection
            inverters = api_client.get_site_inverters(selected_site, selected_skid)
            selected_inverter = render_inverter_selector(inverters)
            
            if selected_inverter:
                navigation_state['inverter_id'] = selected_inverter
                st.session_state.selected_inverter = selected_inverter
    
    return navigation_state


def render_date_range_selector() -> tuple:
    """
    Render date range selector for filtering data.
    
    Returns:
        Tuple of (start_date, end_date)
    """
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(
            "Start Date",
            key="start_date_selector"
        )
    
    with col2:
        end_date = st.date_input(
            "End Date",
            key="end_date_selector"
        )
    
    return start_date, end_date


def render_availability_filter() -> bool:
    """
    Render 100% availability filter toggle.
    
    Returns:
        Boolean indicating if filter is active
    """
    return st.checkbox(
        "Show only 100% availability periods",
        key="availability_filter",
        help="Filter data to show only periods with 100% equipment availability"
    )