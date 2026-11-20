import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from config import Config
from utils.parser import PresentationParser
from utils.ai_generator import AIGenerator
import json

app = Flask(__name__)
app.config.from_object(Config)

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize AI Generator
ai_generator = AIGenerator(api_key=app.config.get('ANTHROPIC_API_KEY'))


@app.route('/')
def index():
    """Render main page"""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and parsing"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': '파일이 없습니다'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'success': False, 'error': '파일이 선택되지 않았습니다'}), 400

    if not Config.allowed_file(file.filename):
        return jsonify({
            'success': False,
            'error': '지원하지 않는 파일 형식입니다. PDF 또는 PPTX 파일만 업로드 가능합니다.'
        }), 400

    try:
        # Save file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Parse file
        parsed_data = PresentationParser.parse_file(filepath)

        if not parsed_data.get('success'):
            return jsonify({
                'success': False,
                'error': f"파일 파싱 실패: {parsed_data.get('error', 'Unknown error')}"
            }), 500

        # Get summary
        summary = PresentationParser.get_summary(parsed_data)

        return jsonify({
            'success': True,
            'filename': filename,
            'summary': summary,
            'parsed_data': parsed_data
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'파일 처리 중 오류 발생: {str(e)}'
        }), 500


@app.route('/generate/script', methods=['POST'])
def generate_script():
    """Generate presentation script"""
    try:
        data = request.get_json()
        parsed_data = data.get('parsed_data')
        total_time = data.get('total_time', 10)
        style = data.get('style', 'professional')

        if not parsed_data:
            return jsonify({'success': False, 'error': '파싱된 데이터가 없습니다'}), 400

        script_data = ai_generator.generate_script(
            parsed_data=parsed_data,
            total_time=total_time,
            style=style
        )

        return jsonify({
            'success': True,
            'script': script_data
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'스크립트 생성 중 오류 발생: {str(e)}'
        }), 500


@app.route('/generate/qa', methods=['POST'])
def generate_qa():
    """Generate expected Q&A"""
    try:
        data = request.get_json()
        parsed_data = data.get('parsed_data')
        count = data.get('count', 5)

        if not parsed_data:
            return jsonify({'success': False, 'error': '파싱된 데이터가 없습니다'}), 400

        qa_data = ai_generator.generate_qa(
            parsed_data=parsed_data,
            count=count
        )

        return jsonify({
            'success': True,
            'qa': qa_data
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Q&A 생성 중 오류 발생: {str(e)}'
        }), 500


@app.route('/generate/tips', methods=['POST'])
def generate_tips():
    """Generate presentation tips and checklist"""
    try:
        data = request.get_json()
        parsed_data = data.get('parsed_data')

        if not parsed_data:
            return jsonify({'success': False, 'error': '파싱된 데이터가 없습니다'}), 400

        tips_data = ai_generator.generate_tips(parsed_data=parsed_data)

        return jsonify({
            'success': True,
            'tips': tips_data
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'팁 생성 중 오류 발생: {str(e)}'
        }), 500


@app.route('/analyze', methods=['POST'])
def analyze_all():
    """Analyze presentation and generate all content"""
    try:
        data = request.get_json()
        parsed_data = data.get('parsed_data')
        total_time = data.get('total_time', 10)
        style = data.get('style', 'professional')
        qa_count = data.get('qa_count', 5)

        if not parsed_data:
            return jsonify({'success': False, 'error': '파싱된 데이터가 없습니다'}), 400

        # Generate all content
        script_data = ai_generator.generate_script(
            parsed_data=parsed_data,
            total_time=total_time,
            style=style
        )

        qa_data = ai_generator.generate_qa(
            parsed_data=parsed_data,
            count=qa_count
        )

        tips_data = ai_generator.generate_tips(parsed_data=parsed_data)

        return jsonify({
            'success': True,
            'script': script_data,
            'qa': qa_data,
            'tips': tips_data
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'분석 중 오류 발생: {str(e)}'
        }), 500


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'ai_enabled': ai_generator.has_api
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
