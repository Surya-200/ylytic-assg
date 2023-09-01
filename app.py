from flask import Flask, request, jsonify
from datetime import datetime
from typing import List, Optional, Dict, Any , Union
import requests

app = Flask(__name__)
API_URL = 'https://app.ylytic.com/ylytic/test'
def fetch_comments() -> list[Dict[str, Union[str, int]]]:
    try:
        response = requests.get(API_URL)
        response.raise_for_status() 
        data = response.json()
        if isinstance(data, List):
            return data
        else:
            app.logger.error("Unexpected data format: %s", data)
            return []
    except requests.RequestException as e:
        app.logger.error("An exception occurred: %s", e)
        return []

def filter_comments(comments: List[Dict[str, Any]], search_params: Dict[str, Any]) -> List[Dict[str, Any]]:
    filtered_comments = []
    for comment in comments:
        if all(
                param_condition(comment, param, value)
                for param, value in search_params.items()
                if value is not None
        ):
            filtered_comments.append(comment)
    return filtered_comments

def param_condition(comment: Dict[str, Any], param: str, value: Any) -> bool:
    if param == 'search_author':
        return value.lower() in comment['author'].lower()
    if param.startswith('at_'):
        comment_date = datetime.strptime(comment['at'], '%d-%m-%Y')
        value_date = datetime.strptime(value, '%d-%m-%Y')
        return comment_date >= value_date if param.endswith('from') else comment_date <= value_date
    if param in ['like_from', 'like_to', 'reply_from', 'reply_to']:
        comment_value = int(comment[param.split('_')[0]])
        value = int(value)
        return comment_value >= value if param.endswith('from') else comment_value <= value
    if param == 'search_text':
        return value.lower() in comment['text'].lower()
    return True

@app.route('/search', methods=['GET'])
def search() -> Any:
    comments = fetch_comments()
    if not comments:
        return jsonify({"error": "Failed to fetch or filter comments"}), 500

    search_params = {
        'search_author': request.args.get('search_author'),
        'at_from': request.args.get('at_from'),
        'at_to': request.args.get('at_to'),
        'like_from': request.args.get('like_from'),
        'like_to': request.args.get('like_to'),
        'reply_from': request.args.get('reply_from'),
        'reply_to': request.args.get('reply_to'),
        'search_text': request.args.get('search_text'),
    }

    filtered_comments = filter_comments(comments, search_params)
    return jsonify(filtered_comments)
if __name__ == '__main__':
    app.run(debug=True)
