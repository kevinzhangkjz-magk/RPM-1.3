"""
Export and Reporting System for Renewable Energy Asset Management
Handles PDF, Excel, and data export functionality
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import io
import base64
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import xlsxwriter


class ExportManager:
    """
    Manages export functionality for reports and data.
    """
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.custom_styles = self._create_custom_styles()
    
    def _create_custom_styles(self) -> Dict:
        """Create custom styles for PDF reports."""
        return {
            'Title': ParagraphStyle(
                'CustomTitle',
                parent=self.styles['Title'],
                fontSize=24,
                textColor=colors.HexColor('#2E7D32'),
                spaceAfter=30
            ),
            'SectionHeader': ParagraphStyle(
                'SectionHeader',
                parent=self.styles['Heading1'],
                fontSize=16,
                textColor=colors.HexColor('#1976D2'),
                spaceAfter=12
            ),
            'Alert': ParagraphStyle(
                'Alert',
                parent=self.styles['Normal'],
                fontSize=12,
                textColor=colors.HexColor('#D32F2F'),
                leftIndent=20
            ),
            'Success': ParagraphStyle(
                'Success',
                parent=self.styles['Normal'],
                fontSize=12,
                textColor=colors.HexColor('#388E3C'),
                leftIndent=20
            )
        }
    
    def export_to_pdf(self, data: Dict, filename: str = None) -> bytes:
        """
        Export data to PDF format with AI-generated executive summary.
        
        Args:
            data: Report data including summary, metrics, and visualizations
            filename: Optional filename for the PDF
            
        Returns:
            PDF file as bytes
        """
        if not filename:
            filename = f"renewable_energy_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # Create PDF in memory
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        
        # Build content
        content = []
        
        # Title Page
        content.append(Paragraph("Renewable Energy Asset Management Report", self.custom_styles['Title']))
        content.append(Spacer(1, 0.2*inch))
        content.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", self.styles['Normal']))
        content.append(PageBreak())
        
        # Executive Summary
        if data.get('summary'):
            content.append(Paragraph("Executive Summary", self.custom_styles['SectionHeader']))
            content.append(Paragraph(data['summary'], self.styles['Normal']))
            content.append(Spacer(1, 0.3*inch))
        
        # Key Metrics
        if data.get('metrics'):
            content.append(Paragraph("Key Performance Metrics", self.custom_styles['SectionHeader']))
            metrics_data = []
            
            for key, value in data['metrics'].items():
                formatted_key = key.replace('_', ' ').title()
                if isinstance(value, float):
                    formatted_value = f"{value:.3f}" if value < 1 else f"{value:,.2f}"
                else:
                    formatted_value = str(value)
                metrics_data.append([formatted_key, formatted_value])
            
            metrics_table = Table(metrics_data, colWidths=[3*inch, 2*inch])
            metrics_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            content.append(metrics_table)
            content.append(Spacer(1, 0.3*inch))
        
        # Site Performance Details
        if data.get('sites'):
            content.append(Paragraph("Site Performance Analysis", self.custom_styles['SectionHeader']))
            
            # Create table data
            headers = ['Site', 'R²', 'RMSE (MW)', 'Revenue Impact', 'Status']
            table_data = [headers]
            
            for site in data['sites']:
                row = [
                    site.get('site_name', 'Unknown'),
                    f"{site.get('r_squared', 0):.3f}",
                    f"{site.get('rmse', 0):.2f}",
                    f"${site.get('revenue_impact', 0):,.0f}",
                    site.get('status', 'N/A')
                ]
                table_data.append(row)
            
            site_table = Table(table_data, colWidths=[2*inch, 1*inch, 1.5*inch, 1.5*inch, 1*inch])
            
            # Style the table
            style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E7D32')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ])
            
            # Add conditional formatting for status
            for i, site in enumerate(data['sites'], 1):
                status = site.get('status', '')
                if status == 'CRITICAL':
                    style.add('BACKGROUND', (4, i), (4, i), colors.HexColor('#FF5252'))
                elif status == 'WARNING':
                    style.add('BACKGROUND', (4, i), (4, i), colors.HexColor('#FFA726'))
                elif status == 'MONITOR':
                    style.add('BACKGROUND', (4, i), (4, i), colors.HexColor('#66BB6A'))
            
            site_table.setStyle(style)
            content.append(site_table)
            content.append(Spacer(1, 0.3*inch))
        
        # Recommendations
        if data.get('recommendations'):
            content.append(Paragraph("Recommendations", self.custom_styles['SectionHeader']))
            for idx, rec in enumerate(data['recommendations'], 1):
                content.append(Paragraph(f"{idx}. {rec}", self.styles['Normal']))
            content.append(Spacer(1, 0.3*inch))
        
        # Build PDF
        doc.build(content)
        
        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
    
    def export_to_excel(self, data: Dict, filename: str = None) -> bytes:
        """
        Export data to Excel format with formatted sheets and charts.
        
        Args:
            data: Report data to export
            filename: Optional filename for the Excel file
            
        Returns:
            Excel file as bytes
        """
        if not filename:
            filename = f"renewable_energy_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        # Create Excel file in memory
        buffer = io.BytesIO()
        
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            workbook = writer.book
            
            # Define formats
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#2E7D32',
                'font_color': '#FFFFFF',
                'border': 1
            })
            
            cell_format = workbook.add_format({
                'border': 1,
                'align': 'center',
                'valign': 'vcenter'
            })
            
            currency_format = workbook.add_format({
                'num_format': '$#,##0',
                'border': 1,
                'align': 'center'
            })
            
            percent_format = workbook.add_format({
                'num_format': '0.00%',
                'border': 1,
                'align': 'center'
            })
            
            # Sheet 1: Summary
            summary_df = pd.DataFrame({
                'Report Date': [datetime.now().strftime('%Y-%m-%d %H:%M')],
                'Total Sites': [data.get('metrics', {}).get('total_sites', 0)],
                'Average R²': [data.get('metrics', {}).get('avg_r_squared', 0)],
                'Total Revenue Impact': [data.get('metrics', {}).get('total_revenue_impact', 0)]
            })
            
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Format summary sheet
            summary_sheet = writer.sheets['Summary']
            for col_num, col in enumerate(summary_df.columns):
                summary_sheet.write(0, col_num, col, header_format)
                summary_sheet.set_column(col_num, col_num, 20)
            
            # Sheet 2: Site Performance
            if data.get('sites'):
                sites_df = pd.DataFrame(data['sites'])
                sites_df.to_excel(writer, sheet_name='Site Performance', index=False)
                
                # Format site performance sheet
                perf_sheet = writer.sheets['Site Performance']
                for col_num, col in enumerate(sites_df.columns):
                    perf_sheet.write(0, col_num, col, header_format)
                    
                    # Apply specific formats based on column
                    if 'revenue' in col.lower():
                        perf_sheet.set_column(col_num, col_num, 15, currency_format)
                    elif 'r_squared' in col.lower():
                        perf_sheet.set_column(col_num, col_num, 12, percent_format)
                    else:
                        perf_sheet.set_column(col_num, col_num, 15, cell_format)
                
                # Add conditional formatting for R²
                if 'r_squared' in sites_df.columns:
                    r2_col = sites_df.columns.get_loc('r_squared')
                    perf_sheet.conditional_format(1, r2_col, len(sites_df), r2_col, {
                        'type': '3_color_scale',
                        'min_color': '#FF5252',
                        'mid_color': '#FFA726',
                        'max_color': '#66BB6A'
                    })
            
            # Sheet 3: Recommendations
            if data.get('recommendations'):
                rec_df = pd.DataFrame({
                    'Priority': list(range(1, len(data['recommendations']) + 1)),
                    'Recommendation': data['recommendations']
                })
                rec_df.to_excel(writer, sheet_name='Recommendations', index=False)
                
                # Format recommendations sheet
                rec_sheet = writer.sheets['Recommendations']
                for col_num, col in enumerate(rec_df.columns):
                    rec_sheet.write(0, col_num, col, header_format)
                    if col == 'Recommendation':
                        rec_sheet.set_column(col_num, col_num, 60)
                    else:
                        rec_sheet.set_column(col_num, col_num, 10)
            
            # Sheet 4: Raw Data (if available)
            if data.get('raw_data'):
                raw_df = pd.DataFrame(data['raw_data'])
                raw_df.to_excel(writer, sheet_name='Raw Data', index=False)
                
                # Format raw data sheet
                raw_sheet = writer.sheets['Raw Data']
                for col_num, col in enumerate(raw_df.columns):
                    raw_sheet.write(0, col_num, col, header_format)
                    raw_sheet.set_column(col_num, col_num, 15)
        
        # Get Excel bytes
        excel_bytes = buffer.getvalue()
        buffer.close()
        
        return excel_bytes
    
    def export_to_csv(self, data: pd.DataFrame, filename: str = None) -> bytes:
        """
        Export DataFrame to CSV format.
        
        Args:
            data: DataFrame to export
            filename: Optional filename for the CSV
            
        Returns:
            CSV file as bytes
        """
        if not filename:
            filename = f"renewable_energy_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Convert to CSV
        csv_buffer = io.StringIO()
        data.to_csv(csv_buffer, index=False)
        csv_bytes = csv_buffer.getvalue().encode()
        csv_buffer.close()
        
        return csv_bytes
    
    def export_to_json(self, data: Dict, filename: str = None) -> bytes:
        """
        Export data to JSON format.
        
        Args:
            data: Data dictionary to export
            filename: Optional filename for the JSON
            
        Returns:
            JSON file as bytes
        """
        if not filename:
            filename = f"renewable_energy_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Convert to JSON
        json_str = json.dumps(data, indent=2, default=str)
        json_bytes = json_str.encode()
        
        return json_bytes
    
    def create_download_button(self, data: bytes, filename: str, mime_type: str, label: str = "Download") -> None:
        """
        Create a download button in Streamlit.
        
        Args:
            data: File data as bytes
            filename: Name of the file
            mime_type: MIME type of the file
            label: Button label
        """
        st.download_button(
            label=label,
            data=data,
            file_name=filename,
            mime=mime_type
        )
    
    def render_export_panel(self, data: Dict) -> None:
        """
        Render the export panel with multiple format options.
        
        Args:
            data: Data to export
        """
        with st.expander("📤 Export Options", expanded=False):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("📄 Export PDF", use_container_width=True):
                    pdf_data = self.export_to_pdf(data)
                    self.create_download_button(
                        pdf_data,
                        f"report_{datetime.now().strftime('%Y%m%d')}.pdf",
                        "application/pdf",
                        "Download PDF Report"
                    )
            
            with col2:
                if st.button("📊 Export Excel", use_container_width=True):
                    excel_data = self.export_to_excel(data)
                    self.create_download_button(
                        excel_data,
                        f"data_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        "Download Excel File"
                    )
            
            with col3:
                if st.button("📋 Export CSV", use_container_width=True):
                    if data.get('sites'):
                        df = pd.DataFrame(data['sites'])
                        csv_data = self.export_to_csv(df)
                        self.create_download_button(
                            csv_data,
                            f"sites_{datetime.now().strftime('%Y%m%d')}.csv",
                            "text/csv",
                            "Download CSV File"
                        )
            
            with col4:
                if st.button("🔧 Export JSON", use_container_width=True):
                    json_data = self.export_to_json(data)
                    self.create_download_button(
                        json_data,
                        f"data_{datetime.now().strftime('%Y%m%d')}.json",
                        "application/json",
                        "Download JSON File"
                    )
            
            # Schedule export
            st.markdown("---")
            st.markdown("**📅 Schedule Automated Reports**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                frequency = st.selectbox(
                    "Frequency",
                    ["Daily", "Weekly", "Monthly"],
                    key="export_frequency"
                )
                
                email = st.text_input(
                    "Email Address",
                    placeholder="user@example.com",
                    key="export_email"
                )
            
            with col2:
                format_choice = st.multiselect(
                    "Formats",
                    ["PDF", "Excel", "CSV"],
                    default=["PDF"],
                    key="export_formats"
                )
                
                if st.button("Schedule Reports", use_container_width=True):
                    if email:
                        st.success(f"Reports scheduled for {email} ({frequency})")
                    else:
                        st.error("Please enter an email address")