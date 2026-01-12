import os  
import re  
import json  
from typing import Dict, List, Set  
from pathlib import Path  
import logging  
from dataclasses import dataclass  
from datetime import datetime
import pandas as pd
import math  

@dataclass  
class IntegrationPattern:  
    pattern_type: str  
    file_path: str  
    line_number: int  
    code_snippet: str  
    data_fields: Set[str]  

@dataclass  
class DemographicData:  
    field_name: str  
    data_type: str  
    occurrences: List[Dict]  

class CodeAnalyzer:  
    def __init__(self, repo_path: str, app_name: str):  
        self.repo_path = Path(repo_path)
        self.app_name = app_name
        self.setup_logging()  

        # Define demographic data patterns  
        self.demographic_patterns = {  
            'id': r'\b(customerId|cm_15|gov_ids?|government_id)\b',
            'name': r'\b(embossed_name|embossed_company_name|primary_name|secondary_name|legal_name|dba_name|double_byte_name|first_name|last_name|full_name|name|amount)\b', 
            'address': r'\b(home_address|business_address|alternate_address|temporary_address|other_address|additional_addresses|address|street|city|state|zip|postal_code)\b',  
            'phone': r'\b(home_phone|alternate_home_phone|business_phone|alternate_business_phone|mobile_phone|alternate_mobile_phone|attorney_phone|fax|ani_phone|other_phone|additional_phone|phone|contact)\b',
            'email': r'\b(servicing_email|estatement_email|business_email|other_email_address|email)\b',
            'identity': r'\b(ssn|social_security|tax_id|passport|gov_ids?|government_id)\b',  
            'demographics': r'\b(gender|dob|date_of_birth|age|nationality|ethnicity|preference_language_cd|member_since_date)\b'  
        }  
    
        self.integration_patterns = {
            'rest_api': {
                'http_methods': r'\b(get|post|put|delete|patch)\b.*\b(api|endpoint)\b',
                'url_patterns': r'https?://[^\s<>"]+|www\.[^\s<>"]+',
                'api_endpoints': r'@RequestMapping|@GetMapping|@PostMapping|@PutMapping|@DeleteMapping'
            },
            'soap_services': {
                'soap_components': r'\b(soap|wsdl|xml)\b',
                'wsdl': r'wsdl|WSDL|\.wsdl|getWSDL|WebService[Client]?',
                'soap_operations': r'SOAPMessage|SOAPEnvelope|SOAPBody|SOAPHeader|SoapClient|SoapBinding',
                'xml_namespaces': r'xmlns[:=]|namespace|schemaLocation',
                'soap_annotations': r'@WebService|@WebMethod|@SOAPBinding|@WebResult|@WebParam',
                'soap_endpoints': r'endpoint[_\s]?url|service[_\s]?url|wsdl[_\s]?url'
            },
            'database': {
                'sql_operations': r'\b(select|insert|update|delete)\s+from|into\b',
                'db_connections': r'jdbc:|connection[_\s]?string|database[_\s]?url'
            },
            'messaging': {
                'kafka': r'kafka|producer|consumer|topic',
                'rabbitmq': r'rabbitmq|amqp',
                'jms': r'jms|queue|topic'
            },
            'file':{
                'file_operations': r'\b(csv|excel|xlsx|json|properties).*(read|write|load|save)\b'
            }
        }
    
        # Supported file extensions
        self.supported_extensions = {  
            '.py': 'Python',  
            '.java': 'Java',  
            '.js': 'JavaScript',  
            '.ts': 'TypeScript',  
            '.cs': 'C#',  
            '.php': 'PHP',  
            '.rb': 'Ruby',
            '.xsd': 'XSD'  
        }  

    def setup_logging(self):  
        logging.basicConfig(  
            level=logging.INFO,  
            format='%(asctime)s - %(levelname)s - %(message)s',  
            handlers=[  
                logging.FileHandler('code_analysis.log', encoding='utf-8'),  
                logging.StreamHandler()  
            ]  
        )  
        self.logger = logging.getLogger(__name__)  

    def scan_repository(self) -> Dict:  
        """  
        Main method to scan the repository and analyze code  
        """  
        results = {
            'metadata': {
                'application_name': self.app_name,
                'scan_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'repository_path': str(self.repo_path)
            },
            'demographic_data': {},
            'integration_patterns': [],
            'summary': {
                'files_analyzed': 0,
                'unique_demographic_fields': set(),
                'demographic_fields_found': 0,
                'integration_patterns_found': 0,
                'file_details': []
            }  
        }  

        try:  
            for file_path in self.get_code_files():  
                self.logger.info(f"Analyzing file: {file_path}")  
                file_results = self.analyze_file(file_path)  
                self.update_results(results, file_results, file_path)  
                results['summary']['files_analyzed'] += 1  

            self.generate_report(results)  
            return results  

        except Exception as e:  
            self.logger.error(f"Error during repository scan: {str(e)}")  
            raise  

    def get_code_files(self) -> List[Path]:  
        """  
        Get all supported code files in the repository  
        """  
        code_files = []  
        for root, _, files in os.walk(self.repo_path):  
            for file in files:  
                file_path = Path(root) / file  
                if file_path.suffix in self.supported_extensions:  
                    code_files.append(file_path)  
        return code_files  

    def analyze_file(self, file_path: Path) -> Dict:  
        """  
        Analyze a single file for demographic data and integration patterns  
        """  
        results = {  
            'demographic_data': {},  
            'integration_patterns': []  
        }  

        try:  
            with open(file_path, 'r', encoding='utf-8-sig') as f:  
                content = f.readlines()  

            for line_num, line in enumerate(content, 1):  
                # Check for demographic data  
                for data_type, pattern in self.demographic_patterns.items():  
                    matches = re.finditer(pattern, line, re.IGNORECASE)  
                    for match in matches:  
                        field_name = match.group(0)  
                        if str(file_path) not in results['demographic_data']:  
                            results['demographic_data'][str(file_path)] = {}  
                        if field_name not in results['demographic_data'][str(file_path)]:  
                            results['demographic_data'][str(file_path)][field_name] = {  
                                'data_type': data_type,  
                                'occurrences': []  
                            }  
                        results['demographic_data'][str(file_path)][field_name]['occurrences'].append({  
                            'line_number': line_num,  
                            'code_snippet': line.strip()  
                        })  

                # Check for integration patterns  
                for pattern_category, sub_patterns in self.integration_patterns.items():
                    for sub_type, pattern in sub_patterns.items():
                        if re.search(pattern, line, re.IGNORECASE):
                            results['integration_patterns'].append({
                                'pattern_type': pattern_category,
                                'sub_type': sub_type,
                                'file_path': str(file_path),
                                'line_number': line_num,
                                'code_snippet': line.strip()
                            })

        except Exception as e:  
            self.logger.error(f"Error analyzing file {file_path}: {str(e)}")  

        return results  

    def update_results(self, main_results: Dict, file_results: Dict, file_path: Path):  
        """  
        Update the main results dictionary with results from a single file  
        """  
        # Update demographic data  
        demographic_fields_count = 0  
        for file, fields in file_results['demographic_data'].items():  
            if file not in main_results['demographic_data']:  
                main_results['demographic_data'][file] = fields  
            else:  
                for field_name, data in fields.items():  
                    if field_name not in main_results['demographic_data'][file]:  
                        main_results['demographic_data'][file][field_name] = data  
                    else:  
                        main_results['demographic_data'][file][field_name]['occurrences'].extend(data['occurrences'])  
            demographic_fields_count += sum(len(data['occurrences']) for data in fields.values())  
            main_results['summary']['unique_demographic_fields'].update(fields.keys())  

        # Update integration patterns  
        integration_patterns_count = len(file_results['integration_patterns'])  
        main_results['integration_patterns'].extend(  
            file_results['integration_patterns']  
        )  

        # Update summary  
        main_results['summary']['demographic_fields_found'] = sum(  
            sum(len(data['occurrences']) for data in fields.values())  
            for fields in main_results['demographic_data'].values()  
        )  
        main_results['summary']['integration_patterns_found'] = len(  
            main_results['integration_patterns']  
        )  

        # Add file details to summary  
        main_results['summary']['file_details'].append({  
            'file_path': str(file_path),  
            'demographic_fields_found': demographic_fields_count,  
            'integration_patterns_found': integration_patterns_count  
        })  

    def analyze_excel_demographic_data(self, excel_file_path: str) -> Dict:
        """
        Analyze Excel file for demographic data based on attr_description
        """
        results = {
            'metadata': {
                'application_name': self.app_name,
                'scan_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'excel_file': excel_file_path
            },
            'demographic_data': {},
            'summary': {
                'total_records': 0,
                'demographic_fields_found': 0,
                'exported_files': []
            }
        }
        
        # Define demographic keywords to search for in attr_description
        demographic_keywords = [
            'embossed name', 'embossed company name', 'primary name', 'secondary name', 
            'legal name', 'dba name', 'double byte name', 'gender', 'dob', 'gov ids', 
            'home address', 'business address', 'alternate address', 'temporary address', 
            'other address', 'additional addresses', 'home phone', 'alternate home phone', 
            'business phone', 'alternate business phone', 'mobile phone', 'alternate mobile phone', 
            'attorney phone', 'fax', 'ani phone', 'other phone', 'additional phone', 
            'servicing email', 'estatement email', 'business email', 'other email address', 
            'preference language cd', 'member since date', 'name', 'address', 'phone', 'email'
        ]
        
        try:
            # Read Excel file
            df = pd.read_excel(excel_file_path)
            results['summary']['total_records'] = len(df)
            
            # Look for attr_description column
            attr_desc_col = None
            for col in df.columns:
                if 'attr_description' in col.lower():
                    attr_desc_col = col
                    break
            
            if not attr_desc_col:
                # If no attr_description column found, look for description column
                for col in df.columns:
                    if 'description' in col.lower():
                        attr_desc_col = col
                        break
            
            if not attr_desc_col:
                raise ValueError("No 'attr_description' or 'description' column found in the Excel file")
            
            # Extract rows where attr_description contains demographic keywords
            demographic_data = []
            for idx, row in df.iterrows():
                if pd.notna(row[attr_desc_col]):
                    description = str(row[attr_desc_col]).lower()
                    # Check if any demographic keyword is present in the description
                    if any(keyword in description for keyword in demographic_keywords):
                        record = {}
                        for col in df.columns:
                            if pd.notna(row[col]):
                                record[col] = row[col]
                        demographic_data.append(record)
            
            results['demographic_data'] = demographic_data
            results['summary']['demographic_fields_found'] = len(demographic_data)
            
            # Export to 20 files
            if demographic_data:
                self.export_demographic_to_files(demographic_data, 20)
                results['summary']['exported_files'] = [f'{self.app_name}_demographic_data_{i+1}.xlsx' for i in range(20)]
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error analyzing Excel file: {str(e)}")
            raise
    
    def export_demographic_to_files(self, data: List[Dict], num_files: int = 20):
        """
        Export demographic data to specified number of files
        """
        if not data:
            return
        
        records_per_file = math.ceil(len(data) / num_files)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        for i in range(num_files):
            start_idx = i * records_per_file
            end_idx = min((i + 1) * records_per_file, len(data))
            
            if start_idx < len(data):
                chunk_data = data[start_idx:end_idx]
                df_chunk = pd.DataFrame(chunk_data)
                
                filename = f'{self.app_name}_demographic_data_{i+1}_{timestamp}.xlsx'
                df_chunk.to_excel(filename, index=False)
                self.logger.info(f"Exported demographic data to: {filename}")

    def generate_report(self, results: Dict):  
        """  
        Generate a detailed HTML report of the analysis  
        """  
        results['summary']['unique_demographic_fields'] = list(results['summary']['unique_demographic_fields'])  

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')  
        html_report = f'{self.app_name}_CodeLens_{timestamp}.html'  
        self.generate_html_report(results, html_report)  

        self.logger.info(f"Analysis report generated: {html_report}")  

    def generate_html_report(self, results: Dict, filename: str):
        """Generate an HTML report for better visualization"""
        self.results = results  # Store results for use in other methods
        unique_fields = list(results['summary']['unique_demographic_fields'])
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{self.app_name} - Code Analysis Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .section {{ margin-bottom: 30px; }}
                .pattern {{ margin-bottom: 20px; padding: 10px; border: 1px solid #ddd; }}
                .code {{ background-color: #f5f5f5; padding: 10px; }}
                table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .metadata {{ background-color: #e9ecef; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{self.app_name} - Code Analysis Report</h1>
                <div class="metadata">
                    <p><strong>Application Name:</strong> {results['metadata']['application_name']}</p>
                    <p><strong>Generated:</strong> {results['metadata']['scan_timestamp']}</p>
                    <p><strong>Repository Path:</strong> {results['metadata']['repository_path']}</p>
                </div>
            </div>
            <div class="section">
                <h2>Summary</h2>
                <p>Files Analyzed: {results['summary']['files_analyzed']}</p>
                <p>Unique Demographic Fields: {len(unique_fields)} [{', '.join(unique_fields)}]</p>
                <p>Demographic Fields Occurrences Found: {results['summary']['demographic_fields_found']}</p>
                <p>Integration Patterns Found: {results['summary']['integration_patterns_found']}</p>

                {self._generate_field_frequency_html(results)}

                {self._generate_demographic_summary_html(results['summary']['file_details'])}
                {self._generate_integration_summary_html(results['summary']['file_details'])}
            </div>

            <div class="section">
                <h2>Demographic Data Fields by File</h2>
                {self._generate_demographic_html(results['demographic_data'])}
            </div>

            <div class="section">
                <h2>Integration Patterns</h2>
                {self._generate_integration_html(results['integration_patterns'])}
            </div>
        </body>
        </html>
        """

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)

    def _generate_demographic_summary_html(self, file_details: List[Dict]) -> str:
        """Generate HTML table for demographic field summary"""
        # Filter out entries with zero demographic fields
        demographic_files = [f for f in file_details if f['demographic_fields_found'] > 0]

        if not demographic_files:
            return ""

        html = """
        <h3>Demographic Fields Summary</h3>
        <table>
            <tr>
                <th>#</th>
                <th>File Analyzed</th>
                <th>Demographic Fields Occurrences</th>
                <th>Fields</th>
            </tr>
        """

        for index, file_detail in enumerate(demographic_files, 1):
            # Get unique fields for this file from demographic_data
            file_path = file_detail['file_path']
            unique_fields = []
            if file_path in self.results['demographic_data']:
                unique_fields = list(self.results['demographic_data'][file_path].keys())

            html += f"""
            <tr>
                <td>{index}</td>
                <td>{file_path}</td>
                <td>{file_detail['demographic_fields_found']}</td>
                <td>{', '.join(unique_fields)}</td>
            </tr>
            """
        return html + "</table>"

    def _generate_integration_summary_html(self, file_details: List[Dict]) -> str:
        """Generate HTML table for integration patterns summary"""
        # Filter out entries with zero integration patterns
        integration_files = [f for f in file_details if f['integration_patterns_found'] > 0]

        if not integration_files:
            return ""

        html = """
        <h3>Integration Patterns Summary</h3>
        <table>
            <tr>
                <th>#</th>
                <th>File Name</th>
                <th>Integration Patterns Found</th>
                <th>Patterns Found Details</th>
            </tr>
        """

        for index, file_detail in enumerate(integration_files, 1):
            # Get pattern details for this file
            file_path = file_detail['file_path']
            pattern_details = set()
            for pattern in self.results['integration_patterns']:
                if pattern['file_path'] == file_path:
                    pattern_details.add(f"{pattern['pattern_type']}: {pattern['sub_type']}")

            html += f"""
            <tr>
                <td>{index}</td>
                <td>{file_detail['file_path']}</td>
                <td>{file_detail['integration_patterns_found']}</td>
                <td>{', '.join(pattern_details)}</td>
            </tr>
            """
        return html + "</table>"

    def _generate_demographic_html(self, demographic_data: Dict) -> str:  
        html = ""  
        for file_path, fields in demographic_data.items():  
            html += f"<h3>File: {file_path}</h3>"  
            for field_name, data in fields.items():  
                html += f"""  
                <div class="pattern">  
                    <h4>Field: {field_name} (Type: {data['data_type']})</h4>  
                    """  
                for occurrence in data['occurrences']:  
                    html += f"""  
                    <div class="code">  
                        <p>Line {occurrence['line_number']}: {occurrence['code_snippet']}</p>  
                    </div>  
                    """  
                html += "</div>"  
        return html  

    def _generate_integration_html(self, integration_patterns: List) -> str:  
        html = ""  
        for pattern in integration_patterns:  
            html += f"""  
            <div class="pattern">
                <h3>Pattern Type: {pattern['pattern_type']}</h3>
                <p>Sub Type: {pattern['sub_type']}</p>
                <p>File: {pattern['file_path']}</p>
                <p>Line: {pattern['line_number']}</p>
                <div class="code">
                    <p>{pattern['code_snippet']}</p>
                </div>
            </div>
            """  
        return html  

    def _generate_field_frequency_html(self, results: Dict) -> str:
        """Generate HTML table for field frequency"""
        # Calculate field frequencies
        field_frequencies = {}
        for file_data in results['demographic_data'].values():
            for field_name, data in file_data.items():
                if field_name not in field_frequencies:
                    field_frequencies[field_name] = {
                        'count': len(data['occurrences']),
                        'type': data['data_type']
                    }
                else:
                    field_frequencies[field_name]['count'] += len(data['occurrences'])

        # Generate HTML table with consistent styling
        html = """
        <div class="section">
            <h3>Field Frequency Analysis</h3>
            <p>Below table shows how many times each demographic field appears across all analyzed files:</p>
            <table>
                <tr>
                    <th style="width: 5%;">#</th>
                    <th style="width: 35%;">Field Name</th>
                    <th style="width: 30%;">Field Type</th>
                    <th style="width: 30%;">Total Occurrences</th>
                </tr>
        """

        for idx, (field_name, data) in enumerate(sorted(field_frequencies.items(), key=lambda x: x[1]['count'], reverse=True), 1):
            html += f"""
                <tr>
                    <td>{idx}</td>
                    <td>{field_name}</td>
                    <td>{data['type']}</td>
                    <td>{data['count']}</td>
                </tr>
            """

        html += """
            </table>
        </div>
        <br>
        """
        return html

def main():  
    """
    Main function to run the code analyzer
    """
    app_name = input("Enter Application/Repository Name: ")
    repo_path = input("Enter the path to your code repository: ")
    
    try:
        analyzer = CodeAnalyzer(repo_path, app_name)  
        results = analyzer.scan_repository()  
        print(f"Analysis complete. Check the generated reports for details.")  
    except Exception as e:
       print(f"Error during analysis: {str(e)}")

if __name__ == "__main__":  
    main()  

# Created/Modified files during execution:  
# - code_analysis.log  
# - code_analysis_report_[timestamp].html