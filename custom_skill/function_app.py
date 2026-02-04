import azure.functions as func
import logging
import json
import re
from typing import List, Dict, Any, Optional

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


def extract_field(content: str, field_name: str) -> Optional[str]:
    """
    Extract a field value from the page_content string.
    
    Args:
        content: The page_content string
        field_name: The field name to extract (e.g., 'id', 'question', 'answer')
        
    Returns:
        The extracted field value or None if not found
    """
    # Pattern to match: field_name: value (until next field or end)
    pattern = rf'{field_name}:\s*(.+?)(?=\n\n(?:id:|question:|answer:)|$)'
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        return match.group(1).strip()
    return None


def process_record(record: Dict[str, Any], index: int = 0) -> Dict[str, Any]:
    """
    Process a single record from Azure AI Search.
    Extracts id, question, and answer from page_content field.
    
    Args:
        record: A dictionary containing optional 'recordId' and 'data' fields
        index: The index of the record (used if recordId is not provided)
        
    Returns:
        A dictionary with 'recordId', 'data', 'errors', and 'warnings'
    """
    try:
        # recordId is optional - use provided value or generate from index
        record_id = record.get('recordId', f'record_{index}')
        data = record.get('data', {})
        
        # Get the page_content field
        page_content = data.get('page_content', '')
        
        if not page_content:
            return {
                'recordId': record_id,
                'data': {},
                'errors': [{'message': 'page_content field is required'}],
                'warnings': []
            }
        
        # Extract id, question, and answer from page_content
        extracted_id = extract_field(page_content, 'id')
        question = extract_field(page_content, 'question')
        answer = extract_field(page_content, 'answer')
        
        # Build the result - only include fields that were found
        result = {}
        
        if extracted_id:
            result['id'] = extracted_id
        
        if question:
            result['question'] = question
            
        if answer:
            result['answer'] = answer
        
        # Only add warnings for critical missing fields (question and answer)
        # id is optional and won't generate a warning
        warnings = []
        if not question:
            warnings.append({'message': 'question field not found in page_content'})
        if not answer:
            warnings.append({'message': 'answer field not found in page_content'})
        
        # Return the processed record
        return {
            'recordId': record_id,
            'data': result,
            'errors': [],
            'warnings': warnings
        }
        
    except Exception as e:
        return {
            'recordId': record.get('recordId', f'record_{index}'),
            'data': {},
            'errors': [{'message': str(e)}],
            'warnings': []
        }


@app.route(route="page_content_split_http_trigger", methods=["POST"])
def page_content_split_http_trigger(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure AI Search custom skill endpoint.
    
    Expects a request body in the format:
    {
        "values": [
            {
                "recordId": "r1",
                "data": {
                    "name": "value"
                }
            }
        ]
    }
    
    Returns a response in the format:
    {
        "values": [
            {
                "recordId": "r1",
                "data": {
                    "greeting": "processed value"
                },
                "errors": [],
                "warnings": []
            }
        ]
    }
    """
    logging.info('Azure AI Search custom skill: Python HTTP trigger function processed a request.')

    try:
        # Parse the request body
        req_body = req.get_json()
        
        if not req_body:
            return func.HttpResponse(
                json.dumps({
                    'error': 'Request body is required'
                }),
                status_code=400,
                mimetype='application/json'
            )
        
        # Get the values array from the request
        values = req_body.get('values')
        
        if not values or not isinstance(values, list):
            return func.HttpResponse(
                json.dumps({
                    'error': 'Invalid request format. Expected "values" array in request body.'
                }),
                status_code=400,
                mimetype='application/json'
            )
        
        # Process each record
        results = []
        for index, record in enumerate(values):
            processed_record = process_record(record, index)
            results.append(processed_record)
        
        # Return the response
        response = {
            'values': results
        }
        
        return func.HttpResponse(
            json.dumps(response, ensure_ascii=False),
            status_code=200,
            mimetype='application/json'
        )
        
    except ValueError as e:
        logging.error(f'Error parsing request body: {str(e)}')
        return func.HttpResponse(
            json.dumps({
                'error': 'Invalid JSON in request body'
            }),
            status_code=400,
            mimetype='application/json'
        )
    except Exception as e:
        logging.error(f'Unexpected error: {str(e)}')
        return func.HttpResponse(
            json.dumps({
                'error': f'Internal server error: {str(e)}'
            }),
            status_code=500,
            mimetype='application/json'
        )