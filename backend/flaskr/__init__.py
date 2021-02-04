import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def paginate_questions(request, selection):
    # helper function to return a paginated list of questions
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions


def read_categories():
    # helper function to read categories and return a dictionary
    categories = Category.query.all()
    category_dict = {}
    for category in categories:
        category_dict[category.id] = category.type
    return category_dict


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    '''
    @DONE: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    '''
    CORS(app)

    '''
    @DONE: Use the after_request decorator to set Access-Control-Allow
    '''
    @app.after_request
    def after_request(response):
        response.headers.add(
            'Access-Control-Allow-Headers',
            'Content-Type,Authorization,true')
        response.headers.add(
            'Access-Control-Allow-Methods',
            'GET,PUT,PATCH,POST,DELETE,OPTIONS')
        return response

    '''
    @DONE:
    Create an endpoint to handle GET requests
    for all available categories.
    '''
    @app.route('/categories')
    def get_categories():
        categories = read_categories()
        return jsonify({'success': True, 'categories': categories
                        })

    '''
    @DONE:
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    TEST 1: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions.
    '''
    @app.route('/questions')
    def get_questions():
        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selection)

        categories = read_categories()

        if len(current_questions) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'questions': current_questions,
            'currentCategory': None,
            'categories': categories,
            'total_questions': len(Question.query.all())
        })

    '''
    @DONE:
    Create an endpoint to DELETE question using a question ID.

    TEST 2: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page.
    '''
    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        question = Question.query.filter(
            Question.id == question_id).one_or_none()

        if question is None:
            abort(404)

        question.delete()
        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selection)

        return jsonify({
            'success': True,
            'deleted': question_id,
            'questions': current_questions,
            'total_questions': len(Question.query.all())})

    '''
    @DONE:
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST 3: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.
    '''
    @app.route('/questions', methods=['POST'])
    def post_question():
        body = request.get_json()

        new_question = body.get('question')
        new_answer = body.get('answer')
        new_category = body.get('category')
        new_difficulty = body.get('difficulty')

        if (new_question == '' or new_answer == ''):
            abort(422)

        question = Question(question=new_question, answer=new_answer,
                            category=new_category, difficulty=new_difficulty)
        question.insert()
        print("Question Added")

        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selection)

        return jsonify({
            'success': True,
            'created': question.id,
            'questions': current_questions,
            'total_questions': len(Question.query.all())
        })

    '''
    @DONE:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST 4: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    '''
    @app.route('/search', methods=['POST'])
    def search_question():
        search_term = request.get_json().get('searchTerm')
        if search_term is None or search_term == '':
            abort(422)
        selection = Question.query.filter(
            Question.question.ilike(
                '%' + search_term + '%')).all()
        current_questions = paginate_questions(request, selection)

        return jsonify({
            'success': True,
            'questions': current_questions,
            'currentCategory': None,
            'total_questions': len(selection)})

    '''
    @DONE:
    Create a GET endpoint to get questions based on category.

    TEST 5: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    '''
    @app.route('/categories/<int:category_id>/questions')
    def get_by_category(category_id):
        questions = Question.query.all()
        category_ids = []
        [category_ids.append(question.category) for question in questions]
        if category_id not in category_ids:
            abort(422)

        selection = Question.query.filter(
            Question.category == category_id).all()
        current_questions = paginate_questions(request, selection)

        return jsonify({
            'success': True,
            'questions': current_questions,
            'currentCategory': category_id,
            'total_questions': len(selection)})

    '''
    @DONE:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST 6: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    '''
    @app.route('/quizzes', methods=['POST'])
    def quiz():
        body = request.get_json()

        previous_questions = body.get('previous_questions')
        quiz_category = body.get('quiz_category')
        quiz_category_id = quiz_category.get('id', 0)

        if quiz_category_id == 0:
            selection = Question.query.filter(
                Question.id.notin_(previous_questions)).all()
        else:
            selection = Question.query.filter_by(
                category=quiz_category_id).filter(
                Question.id.notin_(previous_questions)).all()
        if len(selection) > 0:
            selected_question = selection[random.randrange(0, len(selection))]
            return jsonify({
                'success': True,
                "question": selected_question.format()
            })
        else:
            return jsonify({
                "success": True,
                "question": None
            })

    '''
    @DONE:
    Create error handlers for all expected errors
    including 404 and 422.
    '''
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "Resource Not Found"
        }), 404

    @app.errorhandler(422)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "Unprocessable"
        }), 422

    @app.errorhandler(400)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "Bad Request"
        }), 400

    @app.errorhandler(405)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 405,
            "message": "Method Not Allowed"
        }), 405

    @app.errorhandler(500)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 500,
            "message": "Internal Server Error"
        }), 500

    return app
